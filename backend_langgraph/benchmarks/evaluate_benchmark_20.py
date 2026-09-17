"""统一运行 20 条规划、证据和动态重规划任务。"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx


def upload_materials(client: httpx.Client, base_url: str, materials: list[dict[str, Any]], case_dir: Path) -> list[str]:
    source_ids = []
    for material in materials:
        if material.get("path"):
            fixture = (case_dir / material["path"]).resolve()
            payload = fixture.read_bytes()
            filename = material.get("filename") or fixture.name
        else:
            payload = material["text"].encode("utf-8")
            filename = material["filename"]
        response = client.post(
            f"{base_url}/api/knowledge/upload",
            files={"file": (filename, payload, material.get("content_type", "text/plain"))},
            data={"category": "benchmark-20"},
        )
        response.raise_for_status()
        source_ids.append(response.json()["source_id"])
    return source_ids


def resolve_dynamic_target(plan: dict[str, Any], disruption: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(disruption)
    if not str(result.get("target", "")).startswith("__FIRST_ATTRACTION"):
        return result
    affected = result.get("date")
    day = next((item for item in plan["days"] if item["date"] == affected), None)
    if not day or not day.get("attractions"):
        raise ValueError(f"日期 {affected} 没有可用于闭馆测试的景点")
    result["target"] = day["attractions"][0]["name"]
    result["description"] = f"{result['target']} 临时闭馆"
    return result


def score_plan(plan: dict[str, Any], rubric: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    report = plan.get("validation_report") or {}
    checks = report.get("checks") or {}
    assertions = []
    for check in rubric.get("must_pass", []):
        assertions.append({"name": check, "passed": bool(checks.get(check))})
    assertions.append({
        "name": "minimum_validation_score",
        "passed": float(report.get("score") or 0) >= float(rubric.get("minimum_validation_score", 0)),
        "actual": report.get("score"),
    })
    evidence = plan.get("evidence_report") or {}
    if "expected_evidence_sufficient" in rubric:
        assertions.append({"name": "evidence_sufficient", "passed": evidence.get("sufficient") is rubric["expected_evidence_sufficient"], "actual": evidence.get("sufficient")})
    if rubric.get("allowed_evidence_strategies"):
        assertions.append({"name": "evidence_strategy", "passed": evidence.get("strategy") in rubric["allowed_evidence_strategies"], "actual": evidence.get("strategy")})
    if "minimum_citations" in rubric:
        assertions.append({"name": "minimum_citations", "passed": len(plan.get("citations") or []) >= rubric["minimum_citations"], "actual": len(plan.get("citations") or [])})
    return assertions, all(item["passed"] for item in assertions)


def score_replan(initial: dict[str, Any], revised: dict[str, Any], disruption: dict[str, Any], rubric: dict[str, Any]) -> list[dict[str, Any]]:
    assertions = [{"name": "revision_incremented", "passed": revised.get("revision") == initial.get("revision", 0) + 1}]
    affected = disruption.get("date")
    before = {day["date"]: day for day in initial["days"]}
    after = {day["date"]: day for day in revised["days"]}
    unaffected = [date for date in before if date != affected]
    stability = sum(before[date] == after.get(date) for date in unaffected) / max(len(unaffected), 1)
    assertions.append({"name": "unaffected_plan_stability", "passed": stability >= rubric.get("minimum_plan_stability", 0), "actual": round(stability, 3)})
    if rubric.get("target_must_be_removed") and disruption.get("target"):
        names = [item["name"] for day in revised["days"] if not affected or day["date"] == affected for item in day.get("attractions", [])]
        assertions.append({"name": "closed_target_removed", "passed": disruption["target"] not in names, "actual": disruption["target"]})
    return assertions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("benchmark_20.jsonl"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("benchmark_20_results.json"))
    args = parser.parse_args()
    cases = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    with httpx.Client(timeout=600) as client:
        for index, case in enumerate(cases, start=1):
            started = time.perf_counter()
            request = deepcopy(case["request"])
            try:
                if case.get("materials"):
                    request["knowledge_source_ids"] = upload_materials(client, args.base_url, case["materials"], args.cases.parent)
                initial_response = client.post(f"{args.base_url}/api/trip/plan", json=request)
                initial_response.raise_for_status()
                initial = initial_response.json()["data"]
                plan = initial
                extra_assertions = []
                disruption = None
                if case["task_type"] == "replan":
                    disruption = resolve_dynamic_target(initial, case["disruption"])
                    response = client.post(f"{args.base_url}/api/trip/replan", json={"request": request, "current_plan": initial, "disruption": disruption})
                    response.raise_for_status()
                    plan = response.json()["data"]
                    extra_assertions = score_replan(initial, plan, disruption, case["rubric"])
                assertions, passed = score_plan(plan, case["rubric"])
                assertions.extend(extra_assertions)
                passed = passed and all(item["passed"] for item in extra_assertions)
                manual = case["rubric"].get("manual_assertions", [])
                status = "passed_pending_manual" if passed and manual else ("passed" if passed else "failed")
                result = {"case_id": case["case_id"], "category": case["category"], "status": status, "latency_s": round(time.perf_counter() - started, 2), "assertions": assertions, "manual_assertions": manual, "trace_id": plan.get("planning_trace_id")}
                if disruption:
                    result["resolved_disruption"] = disruption
            except Exception as exc:
                result = {"case_id": case["case_id"], "category": case["category"], "status": "error", "latency_s": round(time.perf_counter() - started, 2), "error": str(exc)}
            results.append(result)
            print(f"[{index:02d}/{len(cases)}] {result['case_id']}: {result['status']}")

    automated_passes = sum(item["status"] in {"passed", "passed_pending_manual"} for item in results)
    summary = {
        "cases": len(results),
        "automated_pass_rate": round(automated_passes / max(len(results), 1), 3),
        "average_latency_s": round(statistics.mean(item["latency_s"] for item in results), 2),
        "status_counts": dict(Counter(item["status"] for item in results)),
        "category_counts": dict(Counter(item["category"] for item in results)),
        "results": results,
    }
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] not in {"failed", "error"} for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
