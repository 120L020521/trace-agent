"""对行程做确定性校验，避免把所有正确性都交给 LLM 判断。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from ..models.schemas import TripPlan, TripRequest, ValidationIssue, ValidationReport


def validate_trip_plan(plan: TripPlan, request: TripRequest, repair_attempted: bool = False) -> ValidationReport:
    issues: List[ValidationIssue] = []
    checks: Dict[str, bool] = {}

    expected_dates = _expected_dates(request)
    actual_dates = [day.date for day in plan.days]
    checks["date_coverage"] = actual_dates == expected_dates
    if not checks["date_coverage"]:
        issues.append(
            ValidationIssue(
                code="DATE_COVERAGE",
                severity="error",
                path="days",
                message="每日行程日期与用户选择的旅行周期不一致",
                expected=str(expected_dates),
                actual=str(actual_dates),
            )
        )

    attraction_ok = True
    meals_ok = True
    coordinates_ok = True
    for index, day in enumerate(plan.days):
        if len(day.attractions) > request.max_daily_attractions:
            attraction_ok = False
            issues.append(
                ValidationIssue(
                    code="DAILY_ATTRACTION_LIMIT",
                    severity="error",
                    path=f"days[{index}].attractions",
                    message="单日景点数量超过用户约束",
                    expected=f"<= {request.max_daily_attractions}",
                    actual=str(len(day.attractions)),
                )
            )
        meal_types = {meal.type for meal in day.meals}
        missing_meals = {"breakfast", "lunch", "dinner"} - meal_types
        if missing_meals:
            meals_ok = False
            issues.append(
                ValidationIssue(
                    code="MISSING_MEAL",
                    severity="warning",
                    path=f"days[{index}].meals",
                    message=f"缺少餐饮安排: {', '.join(sorted(missing_meals))}",
                )
            )
        for attraction_index, attraction in enumerate(day.attractions):
            if attraction.location is None:
                coordinates_ok = False
                issues.append(
                    ValidationIssue(
                        code="UNVERIFIED_COORDINATE",
                        severity="warning",
                        path=f"days[{index}].attractions[{attraction_index}].location",
                        message=f"{attraction.name} 缺少经过地图工具验证的坐标",
                    )
                )
            elif not (-180 <= attraction.location.longitude <= 180 and -90 <= attraction.location.latitude <= 90):
                coordinates_ok = False
                issues.append(
                    ValidationIssue(
                        code="INVALID_COORDINATE",
                        severity="error",
                        path=f"days[{index}].attractions[{attraction_index}].location",
                        message=f"{attraction.name} 的经纬度超出合法范围",
                    )
                )

    checks["daily_attraction_limit"] = attraction_ok
    checks["three_meals"] = meals_ok
    checks["coordinate_validity"] = coordinates_ok

    budget_ok = True
    if request.max_budget is not None:
        actual_budget = plan.budget.total if plan.budget else None
        budget_ok = actual_budget is not None and actual_budget <= request.max_budget
        if not budget_ok:
            issues.append(
                ValidationIssue(
                    code="BUDGET_LIMIT",
                    severity="error",
                    path="budget.total",
                    message="行程总费用超过预算或缺少预算汇总",
                    expected=f"<= {request.max_budget}",
                    actual=str(actual_budget),
                )
            )
    checks["budget_limit"] = budget_ok

    solver_ok = bool(
        plan.optimization_report
        and plan.optimization_report.status in {"OPTIMAL", "FEASIBLE"}
        and not plan.optimization_report.fallback_used
    )
    checks["solver_feasible"] = solver_ok
    if not solver_ok:
        issues.append(
            ValidationIssue(
                code="SOLVER_NOT_FEASIBLE",
                severity="warning",
                path="optimization_report.status",
                message="未获得经过 CP-SAT 证明可行的时间表",
                actual=plan.optimization_report.status if plan.optimization_report else "missing",
            )
        )

    hard_errors = [issue for issue in issues if issue.severity == "error"]
    passed_checks = sum(1 for passed in checks.values() if passed)
    score = passed_checks / max(len(checks), 1)
    return ValidationReport(
        passed=not hard_errors,
        score=round(score, 3),
        issues=issues,
        checks=checks,
        repair_attempted=repair_attempted,
    )


def _expected_dates(request: TripRequest) -> List[str]:
    start = datetime.strptime(request.start_date, "%Y-%m-%d")
    return [
        (start + timedelta(days=offset)).strftime("%Y-%m-%d")
        for offset in range(request.travel_days)
    ]
