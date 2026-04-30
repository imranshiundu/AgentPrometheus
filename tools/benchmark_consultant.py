from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from prometheus_consultant import RuntimeConfig, collect_evidence
from prometheus_json import parse_consultant_json

BENCHMARK_TASKS = [
    {
        "id": "readme_setup_review",
        "task": "Review the README and identify missing setup or verification steps. Do not edit files.",
        "expected_paths_any": ["README.md"],
    },
    {
        "id": "runtime_safety_review",
        "task": "Review consultant runtime safety around patch application, ignored paths, and diagnostics. Do not edit files.",
        "expected_paths_any": ["prometheus_consultant.py"],
    },
    {
        "id": "json_repair_review",
        "task": "Review weak-model JSON handling and identify how invalid consultant responses are normalized. Do not edit files.",
        "expected_paths_any": ["prometheus_json.py"],
    },
]


def score_evidence(packet: Dict[str, Any], expected_paths_any: List[str]) -> Dict[str, Any]:
    selected = [row.get("path") for row in packet.get("selected_files", [])]
    hits = [path for path in expected_paths_any if path in selected]
    compile_errors = packet.get("diagnostics", {}).get("python_compile_errors", [])
    return {
        "selected_count": len(selected),
        "expected_path_hits": hits,
        "expected_path_hit_rate": len(hits) / max(len(expected_paths_any), 1),
        "compile_error_count": len(compile_errors),
        "selected_paths": selected[:25],
    }


def run_benchmarks(workspace: Path, output: Path) -> Dict[str, Any]:
    config = RuntimeConfig(workspace=workspace)
    results: List[Dict[str, Any]] = []
    durations: List[float] = []

    for case in BENCHMARK_TASKS:
        started = time.perf_counter()
        packet = collect_evidence(case["task"], config)
        duration = time.perf_counter() - started
        durations.append(duration)
        result = {
            "id": case["id"],
            "task": case["task"],
            "duration_seconds": round(duration, 4),
            "evidence_score": score_evidence(packet, case["expected_paths_any"]),
            "repo_summary": packet.get("diagnostics", {}).get("repository_summary", ""),
        }
        results.append(result)

    malformed = "```json\n{summary: \"ok\", findings: [\"x\",], confidence: \"medium\",}\n```"
    parsed = parse_consultant_json(malformed)
    json_repair_passed = parsed.get("summary") == "ok" and parsed.get("findings") == ["x"] and parsed.get("confidence") == "medium"

    report = {
        "benchmark_version": 1,
        "workspace": str(workspace),
        "task_count": len(BENCHMARK_TASKS),
        "mean_duration_seconds": round(statistics.mean(durations), 4) if durations else 0,
        "max_duration_seconds": round(max(durations), 4) if durations else 0,
        "json_repair_passed": json_repair_passed,
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic Agent Prometheus consultant benchmarks.")
    parser.add_argument("--workspace", default=".", help="Repository/workspace path to benchmark.")
    parser.add_argument("--output", default="benchmark-results/consultant_benchmark.json", help="Where to write JSON results.")
    args = parser.parse_args()
    report = run_benchmarks(Path(args.workspace).resolve(), Path(args.output))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
