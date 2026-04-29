#!/usr/bin/env python3
"""Watch upstream agent repositories and write safe update reports.

This script does not copy upstream code. It checks public repository metadata,
records the latest observed commit, and creates a local Markdown report whenever
an upstream default branch changes.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "docs" / "upstream_reports" / "state.json"
REPORT_DIR = ROOT / "docs" / "upstream_reports"


@dataclass(frozen=True)
class UpstreamRepo:
    name: str
    owner: str
    repo: str
    default_branch: str
    focus: str


UPSTREAMS: List[UpstreamRepo] = [
    UpstreamRepo(
        name="AutoGPT",
        owner="Significant-Gravitas",
        repo="AutoGPT",
        default_branch="master",
        focus="continuous agents, workflow blocks, frontend lifecycle controls, benchmarks, Agent Protocol",
    ),
    UpstreamRepo(
        name="OpenHands",
        owner="All-Hands-AI",
        repo="OpenHands",
        default_branch="main",
        focus="developer workspace, sandboxing, terminal/file/browser operations, software-engineering UX",
    ),
    UpstreamRepo(
        name="CrewAI",
        owner="crewAIInc",
        repo="crewAI",
        default_branch="main",
        focus="crews, flows, role-based orchestration, event-driven control, observability ideas",
    ),
    UpstreamRepo(
        name="GPT Engineer",
        owner="gpt-engineer-org",
        repo="gpt-engineer",
        default_branch="main",
        focus="spec-to-code planning, clarification loops, file-tree generation, verification cycles",
    ),
]


def github_get(path: str) -> dict:
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "agent-prometheus-upstream-watch",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code} for {path}: {body[:300]}") from exc


def load_state() -> Dict[str, dict]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: Dict[str, dict]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(repo: UpstreamRepo, old_sha: str | None, new_sha: str, commit: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d_%H%M%S")
    path = REPORT_DIR / f"{stamp}_{repo.name.lower().replace(' ', '_')}.md"
    message = commit.get("commit", {}).get("message", "")
    author = commit.get("commit", {}).get("author", {}).get("name", "unknown")
    html_url = commit.get("html_url", "")

    path.write_text(
        f"# Upstream update: {repo.name}\n\n"
        f"- Repository: `{repo.owner}/{repo.repo}`\n"
        f"- Branch: `{repo.default_branch}`\n"
        f"- Previous SHA: `{old_sha or 'first-seen'}`\n"
        f"- Latest SHA: `{new_sha}`\n"
        f"- Commit author: `{author}`\n"
        f"- Commit URL: {html_url}\n"
        f"- Checked at: `{now.isoformat()}`\n\n"
        f"## Commit message\n\n"
        f"```text\n{message}\n```\n\n"
        f"## What Prometheus should inspect\n\n"
        f"{repo.focus}\n\n"
        f"## Safety rule\n\n"
        f"Do not copy upstream code automatically. Review the change, extract the design lesson, then implement original Prometheus code if the idea fits this project.\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    state = load_state()
    changed = False
    reports: List[str] = []

    for repo in UPSTREAMS:
        key = f"{repo.owner}/{repo.repo}"
        commit = github_get(f"/repos/{repo.owner}/{repo.repo}/commits/{repo.default_branch}")
        latest_sha = commit["sha"]
        previous_sha = state.get(key, {}).get("sha")

        if previous_sha != latest_sha:
            report = write_report(repo, previous_sha, latest_sha, commit)
            reports.append(str(report.relative_to(ROOT)))
            state[key] = {
                "sha": latest_sha,
                "branch": repo.default_branch,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            changed = True

    if changed:
        save_state(state)
        print("Upstream changes detected:")
        for report in reports:
            print(f"- {report}")
    else:
        print("No upstream changes detected.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
