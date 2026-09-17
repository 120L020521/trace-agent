"""将用户授权且命中难例规则的 Episode 导出为可审核 JSONL。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.experience_store import ExperienceStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("flywheel_candidates.jsonl"))
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    store = ExperienceStore(args.database)
    candidates = []
    for row in store.hard_cases(args.limit):
        if not row.get("request_json") or not row.get("plan_json"):
            continue
        reasons = []
        if (row.get("validation_score") or 0) < 1:
            reasons.append("validation_score_below_one")
        if row.get("repair_attempted"):
            reasons.append("repair_attempted")
        if row.get("revision", 0) > 0:
            reasons.append("disruption_replan")
        if row.get("solver_status") not in {"OPTIMAL", "FEASIBLE"}:
            reasons.append("solver_not_feasible")
        if row.get("all_feedback_accepted") == 0:
            reasons.append("user_rejected")
        candidates.append(
            {
                "trace_id": row["trace_id"],
                "request": json.loads(row["request_json"]),
                "plan": json.loads(row["plan_json"]),
                "mining_reasons": reasons,
                "quality_signals": {
                    "validation_score": row.get("validation_score"),
                    "solver_status": row.get("solver_status"),
                    "latency_ms": row.get("latency_ms"),
                },
                "review_status": "PENDING_HUMAN_REVIEW",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in candidates),
        encoding="utf-8",
    )
    print(json.dumps({"exported": len(candidates), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
