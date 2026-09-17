"""调用本地 API 跑小型回归集，并汇总约束满足率与延迟。"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("cases.jsonl"))
    args = parser.parse_args()

    cases = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    with httpx.Client(timeout=600) as client:
        for case in cases:
            started = time.perf_counter()
            response = client.post(f"{args.base_url}/api/trip/plan", json=case["request"])
            latency = time.perf_counter() - started
            response.raise_for_status()
            report = response.json()["data"]["validation_report"]
            required = case["rubric"]["must_pass"]
            passed = all(report["checks"].get(check, False) for check in required)
            passed = passed and report["score"] >= case["rubric"]["minimum_validation_score"]
            results.append({"case_id": case["case_id"], "passed": passed, "latency_s": round(latency, 2), "report": report})

    summary = {
        "cases": len(results),
        "pass_rate": round(sum(item["passed"] for item in results) / max(len(results), 1), 3),
        "average_latency_s": round(statistics.mean(item["latency_s"] for item in results), 2),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["pass_rate"] == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
