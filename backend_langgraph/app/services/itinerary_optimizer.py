"""使用 OR-Tools CP-SAT 将 LLM 候选行程转换为满足硬约束的时间表。"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Tuple

from ..models.schemas import Attraction, Budget, DayPlan, OptimizationReport, TripPlan, TripRequest


def optimize_itinerary(plan: TripPlan, request: TripRequest) -> TripPlan:
    started = time.perf_counter()
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        report = OptimizationReport(
            status="ORTOOLS_NOT_INSTALLED",
            fallback_used=True,
            selected_attractions=sum(len(day.attractions) for day in plan.days),
            solver_time_ms=int((time.perf_counter() - started) * 1000),
        )
        return plan.model_copy(update={"optimization_report": report})

    model = cp_model.CpModel()
    selections: Dict[Tuple[int, int], object] = {}
    starts: Dict[Tuple[int, int], object] = {}
    ends: Dict[Tuple[int, int], object] = {}
    objective_terms = []
    travel_terms = []

    day_start = _to_minutes(request.daily_start_time)
    day_end = _to_minutes(request.daily_end_time)

    for day_index, day in enumerate(plan.days):
        intervals = []
        for attraction_index, attraction in enumerate(day.attractions):
            key = (day_index, attraction_index)
            duration = max(30, min(attraction.visit_duration, 8 * 60))
            opening = max(day_start, _to_minutes(attraction.opening_time))
            closing = min(day_end, _to_minutes(attraction.closing_time))
            latest_start = max(opening, closing - duration)

            selected = model.new_bool_var(f"selected_{day_index}_{attraction_index}")
            start_var = model.new_int_var(opening, latest_start, f"start_{day_index}_{attraction_index}")
            end_var = model.new_int_var(opening + duration, closing, f"end_{day_index}_{attraction_index}")
            interval = model.new_optional_interval_var(
                start_var,
                duration,
                end_var,
                selected,
                f"visit_{day_index}_{attraction_index}",
            )
            selections[key] = selected
            starts[key] = start_var
            ends[key] = end_var
            intervals.append(interval)
            utility = attraction.priority_score * 10 + int(attraction.evidence_confidence * 100)
            objective_terms.append(utility * selected)
            if closing - opening < duration:
                model.add(selected == 0)

        if intervals:
            model.add_no_overlap(intervals)
            model.add(sum(selections[(day_index, i)] for i in range(len(day.attractions))) <= request.max_daily_attractions)

        for left in range(len(day.attractions)):
            for right in range(left + 1, len(day.attractions)):
                left_before = model.new_bool_var(f"before_{day_index}_{left}_{right}")
                right_before = model.new_bool_var(f"before_{day_index}_{right}_{left}")
                left_selected = selections[(day_index, left)]
                right_selected = selections[(day_index, right)]
                model.add_bool_or([left_before, right_before, left_selected.Not(), right_selected.Not()])
                model.add_at_most_one(left_before, right_before)
                model.add_implication(left_before, left_selected)
                model.add_implication(left_before, right_selected)
                model.add_implication(right_before, left_selected)
                model.add_implication(right_before, right_selected)

                left_to_right = _travel_minutes(day.attractions[left], day.attractions[right])
                right_to_left = _travel_minutes(day.attractions[right], day.attractions[left])
                model.add(starts[(day_index, right)] >= ends[(day_index, left)] + left_to_right).only_enforce_if(left_before)
                model.add(starts[(day_index, left)] >= ends[(day_index, right)] + right_to_left).only_enforce_if(right_before)
                travel_terms.extend([left_to_right * left_before, right_to_left * right_before])

    if request.max_budget is not None:
        fixed_cost = _fixed_cost(plan)
        attraction_budget = max(0, request.max_budget - fixed_cost)
        ticket_terms = []
        for day_index, day in enumerate(plan.days):
            for attraction_index, attraction in enumerate(day.attractions):
                ticket_terms.append(attraction.ticket_price * selections[(day_index, attraction_index)])
        model.add(sum(ticket_terms) <= attraction_budget)

    model.maximize(sum(objective_terms) - sum(travel_terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 3.0
    # 单 worker 在 Windows/Conda 混合环境中更稳定；候选景点规模很小，性能足够。
    solver.parameters.num_search_workers = 1
    status = solver.solve(model)
    status_name = solver.status_name(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        report = OptimizationReport(
            status=status_name,
            fallback_used=True,
            selected_attractions=sum(len(day.attractions) for day in plan.days),
            solver_time_ms=int((time.perf_counter() - started) * 1000),
        )
        return plan.model_copy(update={"optimization_report": report})

    optimized_days: List[DayPlan] = []
    dropped: List[str] = []
    selected_count = 0
    estimated_travel = 0
    for day_index, day in enumerate(plan.days):
        scheduled = []
        for attraction_index, attraction in enumerate(day.attractions):
            key = (day_index, attraction_index)
            if solver.value(selections[key]):
                start_minute = solver.value(starts[key])
                end_minute = solver.value(ends[key])
                scheduled.append(
                    attraction.model_copy(
                        update={
                            "scheduled_start": _format_minutes(start_minute),
                            "scheduled_end": _format_minutes(end_minute),
                        }
                    )
                )
                selected_count += 1
            else:
                dropped.append(attraction.name)
        scheduled.sort(key=lambda attraction: attraction.scheduled_start or "99:99")
        estimated_travel += sum(
            _travel_minutes(scheduled[index], scheduled[index + 1])
            for index in range(max(0, len(scheduled) - 1))
        )
        optimized_days.append(day.model_copy(update={"attractions": scheduled}))

    report = OptimizationReport(
        status=status_name,
        objective_value=round(solver.objective_value, 2),
        selected_attractions=selected_count,
        dropped_attractions=dropped,
        estimated_travel_minutes=estimated_travel,
        solver_time_ms=int((time.perf_counter() - started) * 1000),
    )
    optimized_budget = plan.budget
    if plan.budget:
        attraction_total = sum(
            attraction.ticket_price
            for day in optimized_days
            for attraction in day.attractions
        )
        optimized_budget = plan.budget.model_copy(
            update={
                "total_attractions": attraction_total,
                "total": _fixed_cost(plan) + attraction_total,
            }
        )
    return plan.model_copy(
        update={"days": optimized_days, "budget": optimized_budget, "optimization_report": report}
    )


def _fixed_cost(plan: TripPlan) -> int:
    if not plan.budget:
        return 0
    return plan.budget.total_hotels + plan.budget.total_meals + plan.budget.total_transportation


def _to_minutes(value: str) -> int:
    try:
        hour, minute = value.split(":", 1)
        return int(hour) * 60 + int(minute)
    except (AttributeError, TypeError, ValueError):
        return 9 * 60


def _format_minutes(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def _travel_minutes(origin: Attraction, destination: Attraction) -> int:
    if not origin.location or not destination.location:
        return 30
    radius_km = 6371.0
    lat1 = math.radians(origin.location.latitude)
    lat2 = math.radians(destination.location.latitude)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(destination.location.longitude - origin.location.longitude)
    haversine = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    distance_km = radius_km * 2 * math.asin(math.sqrt(haversine))
    # 城市公共交通的保守近似：平均 20km/h，另加 10 分钟换乘缓冲。
    return max(10, int(distance_km / 20 * 60) + 10)
