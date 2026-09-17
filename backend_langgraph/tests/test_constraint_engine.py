from app.models.schemas import (
    Attraction,
    Budget,
    DayPlan,
    Meal,
    TripPlan,
    TripRequest,
)
from app.services.constraint_engine import validate_trip_plan


def _request(**updates):
    payload = {
        "city": "北京",
        "start_date": "2026-10-01",
        "end_date": "2026-10-01",
        "travel_days": 1,
        "transportation": "公共交通",
        "accommodation": "经济型酒店",
        "max_budget": 500,
        "max_daily_attractions": 2,
    }
    payload.update(updates)
    return TripRequest(**payload)


def _plan(attraction_count=1, total=400):
    return TripPlan(
        city="北京",
        start_date="2026-10-01",
        end_date="2026-10-01",
        days=[
            DayPlan(
                date="2026-10-01",
                day_index=0,
                description="北京一日游",
                transportation="公共交通",
                accommodation="经济型酒店",
                attractions=[
                    Attraction(
                        name=f"景点{index}",
                        address="北京市",
                        visit_duration=120,
                        description="测试景点",
                    )
                    for index in range(attraction_count)
                ],
                meals=[
                    Meal(type="breakfast", name="早餐"),
                    Meal(type="lunch", name="午餐"),
                    Meal(type="dinner", name="晚餐"),
                ],
            )
        ],
        overall_suggestions="测试",
        budget=Budget(total=total),
    )


def test_hard_constraints_trigger_repair_signal():
    report = validate_trip_plan(_plan(attraction_count=3, total=800), _request())

    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {"DAILY_ATTRACTION_LIMIT", "BUDGET_LIMIT"}


def test_unverified_coordinate_is_warning_not_hard_failure():
    report = validate_trip_plan(_plan(), _request())

    assert report.passed is True
    assert "UNVERIFIED_COORDINATE" in {issue.code for issue in report.issues}
