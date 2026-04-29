from __future__ import annotations

import asyncio
import fnmatch
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import redis
from openai import OpenAI

DEFAULT_IGNORE = [
    ".git/**", "**/.git/**", "node_modules/**", "**/node_modules/**",
    "venv/**", "**/venv/**", "__pycache__/**", "**/__pycache__/**",
    "workspace/hive_mind_db/**", "**/*.png", "**/*.jpg", "**/*.jpeg",
    "**/*.gif", "**/*.webp", "**/*.pdf", "**/*.zip", "**/*.db",
    "**/*.sqlite", ".env", "**/.env",
]

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".txt",
    ".yml", ".yaml", ".toml", ".ini", ".css", ".html", ".sh",
    ".dockerfile",
}

SPECIAL_TEXT_FILENAMES = {"Dockerfile", "Makefile"}


@dataclass
class RuntimeConfig:
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    workspace: Path = Path(os.getenv("PROMETHEUS_WORKSPACE", "workspace"))
    api_base: str = os.getenv("OPENAI_API_BASE", "http://litellm:4000/v1")
    api_key: str = os.getenv("OPENAI_API_KEY", os.getenv("LITELLM_API_KEY", "sk-prometheus-local"))
    consultant_model: str = os.getenv("PROMETHEUS_CONSULTANT_MODEL", "consultant-model")
    max_files: int = int(os.getenv("PROMETHEUS_MAX_FILES", "80"))
    max_file_chars: int = int(os.getenv("PROMETHEUS_MAX_FILE_CHARS", "4000"))
    evidence_budget: int = int(os.getenv("PROMETHEUS_EVIDENCE_BUDGET", "22000"))
    auto_apply: bool = os.getenv("PROMETHEUS_AUTO_APPLY", "false").lower() == "true"


def make_redis(config: RuntimeConfig) -> redis.Redis:
    return redis.Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)


def log(r: redis.Redis, message: str, kind: str = "system") -> None:
    payload = {"time": datetime.now().strftime("%H:%M:%S"), "type": kind, "msg": message}
    r.lpush("prometheus_logs", json.dumps(payload))
    r.ltrim("prometheus_logs", 0, 500)
    print(f"[{kind.upper()}] {message}")


def notify(r: redis.Redis, text: str, chat_id: Optional[int] = None, approval_gate: bool = False) -> None:
    payload: Dict[str, Any] = {"text": text, "approval_gate": approval_gate}
    if chat_id is not None:
        payload["chat_id"] = chat_id
    r.lpush("prometheus_notifications", json.dumps(payload))


def load_ignore_patterns(workspace: Path) -> List[str]:
    patterns = list(DEFAULT_IGNORE)
    ignore_file = workspace.parent / ".prometheusignore"
    if ignore_file.exists():
        for line in ignore_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def ignored(rel_path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, p) or fnmatch.fnmatch(Path(rel_path).name, p) for p in patterns)


def is_text_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in TEXT_EXTENSIONS or path.name in SPECIAL_TEXT_FILENAMES


def safe_rel(workspace: Path, path: Path) -> Optional[str]:
    try:
        return str(path.resolve().relative_to(workspace.resolve()))
    except ValueError:
        return None


def iter_files(config: RuntimeConfig) -> List[Path]:
    config.workspace.mkdir(parents=True, exist_ok=True)
    patterns = load_ignore_patterns(config.workspace)
    files: List[Path] = []
    for path in config.workspace.rglob("*"):
        if not path.is_file():
            continue
        rel = safe_rel(config.workspace, path)
        if rel and not ignored(rel, patterns) and is_text_file(path):
            files.append(path)
    return sorted(files, key=lambda p: str(p))[: config.max_files]


def sample_file(path: Path, limit: int) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n...[middle omitted]...\n" + text[-half:]


def score_file(task: str, rel: str, sample: str) -> int:
    terms = {w.lower() for w in task.replace("_", " ").replace("/", " ").split() if len(w) > 2}
    haystack = f"{rel}\n{sample[:1500]}".lower()
    return sum(haystack.count(term) for term in terms)


def compile_checks(files: List[Path], workspace: Path) -> List[Dict[str, str]]:
    """Run Python syntax diagnostics without writing .pyc files to the workspace."""
    errors: List[Dict[str, str]] = []
    for path in files:
        if path.suffix != ".py":
            continue
        rel = safe_rel(workspace, path) or str(path)
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            compile(source, rel, "exec")
        except Exception as exc:
            errors.append({"file": rel, "error": str(exc)})
    return errors


def collect_evidence(task: str, config: RuntimeConfig) -> Dict[str, Any]:
    files = iter_files(config)
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for path in files:
        rel = safe_rel(config.workspace, path)
        if not rel:
            continue
        sample = sample_file(path, config.max_file_chars)
        scored.append((score_file(task, rel, sample), {"path": rel, "size": path.stat().st_size, "sample": sample}))
    scored.sort(key=lambda row: row[0], reverse=True)

    selected: List[Dict[str, Any]] = []
    used = 0
    for _, item in scored:
        cost = len(json.dumps(item, ensure_ascii=False))
        if selected and used + cost > config.evidence_budget:
            break
        selected.append(item)
        used += cost

    return {
        "task": task,
        "mode": "consultant_architecture",
        "principle": "The runtime executes. The AI consults.",
        "rules": [
            "Use only supplied evidence.",
            "Do not claim commands were run unless logs prove it.",
            "Ask for missing evidence instead of guessing.",
            "Prefer small safe steps for weak models.",
        ],
        "repo_map": [{"path": safe_rel(config.workspace, p), "size": p.stat().st_size} for p in files],
        "selected_files": selected,
        "diagnostics": {"python_compile_errors": compile_checks(files, config.workspace)},
    }


def system_prompt() -> str:
    return (
        "You are the consultant layer inside Agent Prometheus. Return valid JSON only. "
        "You do not execute commands and you do not know hidden files. "
        "Use the evidence packet. Return: summary, findings, plan, tests_to_run, risks, missing_evidence, confidence. "
        "Keep the answer practical for a small or weak model."
    )


def parse_json(raw: str) -> Dict[str, Any]:
    try:
        return json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except Exception:
                pass
    return {"summary": raw[:2000], "findings": [], "plan": [], "tests_to_run": [], "risks": ["Model returned non-JSON output."], "missing_evidence": [], "confidence": "low"}


def ask_model(packet: Dict[str, Any], config: RuntimeConfig) -> Dict[str, Any]:
    client = OpenAI(base_url=config.api_base, api_key=config.api_key)
    response = client.chat.completions.create(
        model=config.consultant_model,
        temperature=0.1,
        max_tokens=1600,
        messages=[
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": json.dumps(packet, ensure_ascii=False)},
        ],
    )
    return parse_json(response.choices[0].message.content or "{}")


def render_report(task: str, result: Dict[str, Any], diagnostics: Dict[str, Any]) -> str:
    return json.dumps({"task": task, "result": result, "diagnostics": diagnostics}, indent=2, ensure_ascii=False)


async def handle_task(payload: Dict[str, Any], config: RuntimeConfig, r: redis.Redis) -> None:
    task = (payload.get("task") or "").strip()
    chat_id = payload.get("chat_id")
    if not task:
        return
    log(r, f"Evidence scan started: {task[:160]}", "scanner")
    packet = collect_evidence(task, config)
    log(r, f"Evidence ready: {len(packet['selected_files'])} files selected", "scanner")
    result = ask_model(packet, config)
    report = render_report(task, result, packet["diagnostics"])
    notify(r, "Consultant report:\n\n```json\n" + report[:3500] + "\n```", chat_id=chat_id)
    log(r, "Consultant report sent", "consultant")


async def poll() -> None:
    config = RuntimeConfig()
    r = make_redis(config)
    log(r, "Agent Prometheus consultant runtime online", "system")
    while True:
        if r.get("prometheus_kill_switch") == "true":
            r.delete("prometheus_kill_switch")
            log(r, "Kill switch received. Runtime paused.", "system")
            break
        raw = r.rpop("prometheus_tasks")
        if raw:
            try:
                await handle_task(json.loads(raw), config, r)
            except Exception as exc:
                log(r, f"Task failed safely: {exc}", "system")
                notify(r, f"Task failed safely: {exc}")
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(poll())
