"""评测扰动恢复成功率和未受影响行程稳定度。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("disruptions.jsonl"))
    args = parser.parse_args()

    cases = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    with httpx.Client(timeout=600) as client:
        for case in cases:
            initial_response = client.post(f"{args.base_url}/api/trip/plan", json=case["request"])
            initial_response.raise_for_status()
            initial_plan = initial_response.json()["data"]

            replan_response = client.post(
                f"{args.base_url}/api/trip/replan",
                json={"request": case["request"], "current_plan": initial_plan, "disruption": case["disruption"]},
            )
            replan_response.raise_for_status()
            revised_plan = replan_response.json()["data"]
            affected_date = case["disruption"].get("date")
            original_days = {day["date"]: day for day in initial_plan["days"]}
            revised_days = {day["date"]: day for day in revised_plan["days"]}
            unaffected = [date for date in original_days if date != affected_date]
            stable = sum(original_days[date] == revised_days.get(date) for date in unaffected)
            stability = stable / max(len(unaffected), 1)
            target = case["disruption"].get("target")
            target_removed = True
            if target:
                target_removed = all(
                    attraction["name"] != target
                    for day in revised_plan["days"]
                    if not affected_date or day["date"] == affected_date
                    for attraction in day["attractions"]
                )
            recovered = revised_plan["revision"] == initial_plan.get("revision", 0) + 1 and target_removed
            results.append({"case_id": case["case_id"], "recovered": recovered, "plan_stability": round(stability, 3)})

    summary = {
        "cases": len(results),
        "recovery_rate": round(sum(item["recovered"] for item in results) / max(len(results), 1), 3),
        "average_plan_stability": round(sum(item["plan_stability"] for item in results) / max(len(results), 1), 3),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["recovery_rate"] == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
