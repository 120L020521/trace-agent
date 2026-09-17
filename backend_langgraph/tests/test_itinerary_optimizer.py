from app.models.schemas import Attraction, Budget, DayPlan, TripPlan, TripRequest
from app.services.itinerary_optimizer import optimize_itinerary


def test_cp_sat_respects_budget_and_daily_limit():
    request = TripRequest(
        city="北京",
        start_date="2026-10-01",
        end_date="2026-10-01",
        travel_days=1,
        transportation="公共交通",
        accommodation="经济型酒店",
        max_budget=180,
        max_daily_attractions=2,
    )
    candidates = [
        Attraction(name="故宫", address="北京", visit_duration=120, description="A", ticket_price=60, priority_score=95),
        Attraction(name="国博", address="北京", visit_duration=120, description="B", ticket_price=0, priority_score=90),
        Attraction(name="远郊景点", address="北京", visit_duration=180, description="C", ticket_price=160, priority_score=20),
    ]
    plan = TripPlan(
        city="北京",
        start_date="2026-10-01",
        end_date="2026-10-01",
        days=[DayPlan(date="2026-10-01", day_index=0, description="候选", transportation="公共交通", accommodation="经济型酒店", attractions=candidates)],
        overall_suggestions="测试",
        budget=Budget(total_attractions=220, total=220),
    )

    optimized = optimize_itinerary(plan, request)

    assert optimized.optimization_report.status in {"OPTIMAL", "FEASIBLE"}
    assert {item.name for item in optimized.days[0].attractions} == {"故宫", "国博"}
    assert all(item.scheduled_start and item.scheduled_end for item in optimized.days[0].attractions)
    assert optimized.budget.total <= request.max_budget
    assert "远郊景点" in optimized.optimization_report.dropped_attractions
