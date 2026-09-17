from pathlib import Path

from app.models.schemas import Budget, DayPlan, TripPlan, TripRequest, ValidationReport
from app.services.experience_store import ExperienceStore


def test_data_flywheel_requires_consent_for_full_payload(tmp_path: Path):
    store = ExperienceStore(tmp_path / "experience.db")
    request = TripRequest(
        city="北京",
        start_date="2026-10-01",
        end_date="2026-10-01",
        travel_days=1,
        transportation="公共交通",
        accommodation="经济型酒店",
        free_text_input="私人偏好",
        enable_experience_learning=False,
    )
    plan = TripPlan(
        city="北京",
        start_date="2026-10-01",
        end_date="2026-10-01",
        days=[DayPlan(date="2026-10-01", day_index=0, description="test", transportation="公共交通", accommodation="酒店")],
        overall_suggestions="test",
        budget=Budget(total=100),
        validation_report=ValidationReport(passed=True, score=1.0),
        planning_trace_id="trace-no-consent",
    )

    store.save_episode("trace-no-consent", request, plan, 10)
    episode = store.get_trace("trace-no-consent")["episode"]

    assert episode["request_json"] is None
    assert episode["plan_json"] is None
    assert episode["request_fingerprint"]


def test_rejected_consented_episode_becomes_hard_case(tmp_path: Path):
    store = ExperienceStore(tmp_path / "experience.db")
    request = TripRequest(
        city="上海",
        start_date="2026-10-01",
        end_date="2026-10-01",
        travel_days=1,
        transportation="公共交通",
        accommodation="酒店",
        enable_experience_learning=True,
    )
    plan = TripPlan(
        city="上海",
        start_date="2026-10-01",
        end_date="2026-10-01",
        days=[DayPlan(date="2026-10-01", day_index=0, description="test", transportation="公共交通", accommodation="酒店")],
        overall_suggestions="test",
        validation_report=ValidationReport(passed=True, score=1.0),
        planning_trace_id="trace-consent",
    )
    store.save_episode("trace-consent", request, plan, 20)
    store.add_feedback("trace-consent", accepted=False, rating=2, comment="路线太绕")

    hard_cases = store.hard_cases()

    assert [case["trace_id"] for case in hard_cases] == ["trace-consent"]
    assert hard_cases[0]["all_feedback_accepted"] == 0
