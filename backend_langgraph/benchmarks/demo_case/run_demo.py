"""稳定演示：上传资料 -> 规划 -> 自动选择景点模拟闭馆 -> 局部重规划。"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--start-after-days", type=int, default=7)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("demo_output.json"))
    parser.add_argument("--skip-image", action="store_true", help="仅上传文字资料，用于无视觉模型的环境")
    args = parser.parse_args()
    case_dir = Path(__file__).parent
    request = json.loads((case_dir / "demo_request.json").read_text(encoding="utf-8"))
    start = date.today() + timedelta(days=args.start_after_days)
    request["start_date"] = start.isoformat()
    request["end_date"] = (start + timedelta(days=request["travel_days"] - 1)).isoformat()

    with httpx.Client(timeout=600) as client:
        health = client.get(f"{args.base_url}/health")
        health.raise_for_status()
        health_data = health.json()
        if not health_data.get("agent_ready"):
            raise RuntimeError(f"Agent Runtime 未就绪: {health_data.get('checks')}")

        materials = [(case_dir / "beijing_material.md", "text/markdown")]
        if not args.skip_image:
            materials.append((case_dir.parent / "fixtures" / "beijing_constraint_card.png", "image/png"))
        sources = []
        for material_path, content_type in materials:
            upload = client.post(
                f"{args.base_url}/api/knowledge/upload",
                files={"file": (material_path.name, material_path.read_bytes(), content_type)},
                data={"category": "stable-demo"},
            )
            upload.raise_for_status()
            sources.append(upload.json())
        request["knowledge_source_ids"] = [source["source_id"] for source in sources]

        planned = client.post(f"{args.base_url}/api/trip/plan", json=request)
        planned.raise_for_status()
        initial = planned.json()["data"]
        affected_day = initial["days"][1]
        if not affected_day.get("attractions"):
            raise RuntimeError("第二天没有景点，无法执行闭馆演示")
        closed_target = affected_day["attractions"][0]["name"]
        disruption = {
            "type": "attraction_closed",
            "date": affected_day["date"],
            "target": closed_target,
            "description": f"{closed_target} 临时闭馆",
        }
        replanned = client.post(
            f"{args.base_url}/api/trip/replan",
            json={"request": request, "current_plan": initial, "disruption": disruption},
        )
        replanned.raise_for_status()
        revised = replanned.json()["data"]

    initial_by_date = {day["date"]: day for day in initial["days"]}
    revised_by_date = {day["date"]: day for day in revised["days"]}
    unaffected_dates = [day for day in initial_by_date if day != disruption["date"]]
    checks = {
        "initial_constraints_passed": bool(initial.get("validation_report", {}).get("passed")),
        "evidence_strategy_visible": bool(initial.get("evidence_report", {}).get("strategy")),
        "revision_incremented": revised.get("revision") == initial.get("revision", 0) + 1,
        "closed_target_removed": all(item["name"] != closed_target for item in revised_by_date[disruption["date"]].get("attractions", [])),
        "unaffected_days_preserved": all(initial_by_date[day] == revised_by_date.get(day) for day in unaffected_dates),
        "trace_changed": initial.get("planning_trace_id") != revised.get("planning_trace_id"),
    }
    output = {
        "request": request,
        "uploaded_sources": sources,
        "disruption": disruption,
        "checks": checks,
        "passed": all(checks.values()),
        "initial_plan": initial,
        "revised_plan": revised,
    }
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": output["passed"], "checks": checks, "initial_trace": initial.get("planning_trace_id"), "revised_trace": revised.get("planning_trace_id"), "output": str(args.output)}, ensure_ascii=False, indent=2))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
