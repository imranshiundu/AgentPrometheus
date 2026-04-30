from __future__ import annotations

import asyncio
import fnmatch
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import redis
from openai import OpenAI

from prometheus_indexer import index_repository, summarize_index
from prometheus_json import parse_consultant_json

DEFAULT_IGNORE = [
    ".git/**", "**/.git/**", "node_modules/**", "**/node_modules/**",
    "venv/**", "**/venv/**", "__pycache__/**", "**/__pycache__/**",
    "hive_mind_db/**", "**/hive_mind_db/**", "workspace/hive_mind_db/**",
    "**/*.png", "**/*.jpg", "**/*.jpeg", "**/*.gif", "**/*.webp",
    "**/*.pdf", "**/*.zip", "**/*.db", "**/*.sqlite", ".env", "**/.env",
]

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".txt",
    ".yml", ".yaml", ".toml", ".ini", ".css", ".html", ".sh", ".dockerfile",
}
SPECIAL_TEXT_FILENAMES = {"Dockerfile", "Makefile"}
PROTECTED_PATH_PARTS = {".git", "node_modules", "venv", "__pycache__", "hive_mind_db"}


@dataclass
class RuntimeConfig:
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    workspace: Path = Path(os.getenv("PROMETHEUS_WORKSPACE", "workspace"))
    api_base: str = os.getenv("OPENAI_API_BASE", "http://litellm:4000/v1")
    api_key: str = os.getenv("OPENAI_API_KEY", os.getenv("LITELLM_API_KEY", "sk-prometheus-dummy"))
    consultant_model: str = os.getenv("PROMETHEUS_CONSULTANT_MODEL", "consultant-model")
    cheap_model: str = os.getenv("PROMETHEUS_CHEAP_MODEL", "utility-model")
    max_files: int = int(os.getenv("PROMETHEUS_MAX_FILES", "120"))
    max_file_chars: int = int(os.getenv("PROMETHEUS_MAX_FILE_CHARS", "6000"))
    evidence_budget: int = int(os.getenv("PROMETHEUS_EVIDENCE_BUDGET", "28000"))
    approval_timeout: int = int(os.getenv("PROMETHEUS_APPROVAL_TIMEOUT", "1800"))
    auto_apply: bool = os.getenv("PROMETHEUS_AUTO_APPLY", "false").lower() == "true"


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def make_redis(config: RuntimeConfig) -> redis.Redis:
    return redis.Redis(host=config.redis_host, port=config.redis_port, decode_responses=True, socket_connect_timeout=3, socket_timeout=3)


def dashboard_log(r: redis.Redis, msg: str, agent: str = "consultant") -> None:
    payload = {"time": now(), "type": agent.lower(), "msg": msg}
    try:
        r.lpush("prometheus_logs", json.dumps(payload))
        r.ltrim("prometheus_logs", 0, 500)
    finally:
        print(f"[{agent.upper()}] {msg}")


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


def is_ignored(rel_path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, p) or fnmatch.fnmatch(Path(rel_path).name, p) for p in patterns)


def is_text_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in TEXT_EXTENSIONS or path.name in SPECIAL_TEXT_FILENAMES or path.name.endswith(".Dockerfile")


def safe_rel(workspace: Path, path: Path) -> Optional[str]:
    try:
        return str(path.resolve().relative_to(workspace.resolve()))
    except ValueError:
        return None


def iter_repo_files(config: RuntimeConfig) -> List[Path]:
    config.workspace.mkdir(parents=True, exist_ok=True)
    patterns = load_ignore_patterns(config.workspace)
    files: List[Path] = []
    for path in config.workspace.rglob("*"):
        if not path.is_file():
            continue
        rel = safe_rel(config.workspace, path)
        if rel is None or is_ignored(rel, patterns) or not is_text_file(path):
            continue
        files.append(path)
    return sorted(files, key=lambda p: str(p))[: config.max_files]


def read_sample(path: Path, max_chars: int) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n...[middle omitted for token budget]...\n\n" + text[-half:]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:12]


def score_file(task: str, rel_path: str, text: str) -> int:
    terms = {w.lower() for w in task.replace("/", " ").replace("_", " ").split() if len(w) > 2}
    haystack = f"{rel_path}\n{text[:2000]}".lower()
    return sum(haystack.count(term) for term in terms)


def compile_python(paths: List[Path], workspace: Path) -> List[Dict[str, str]]:
    """Run Python syntax diagnostics without writing .pyc files."""
    failures: List[Dict[str, str]] = []
    for path in paths:
        if path.suffix != ".py":
            continue
        rel = safe_rel(workspace, path) or str(path)
        try:
            compile(path.read_text(encoding="utf-8", errors="ignore"), rel, "exec")
        except Exception as exc:
            failures.append({"file": rel, "error": str(exc)})
    return failures


def collect_evidence(task: str, config: RuntimeConfig) -> Dict[str, Any]:
    files = iter_repo_files(config)
    file_rows: List[Tuple[int, Dict[str, Any]]] = []
    total_chars = 0
    for path in files:
        rel = safe_rel(config.workspace, path)
        if rel is None:
            continue
        sample = read_sample(path, config.max_file_chars)
        file_rows.append((score_file(task, rel, sample), {"path": rel, "size": path.stat().st_size, "sha": sha(sample), "sample": sample}))

    file_rows.sort(key=lambda row: row[0], reverse=True)
    selected: List[Dict[str, Any]] = []
    for _, meta in file_rows:
        estimated = len(json.dumps(meta, ensure_ascii=False))
        if selected and total_chars + estimated > config.evidence_budget:
            break
        selected.append(meta)
        total_chars += estimated

    repo_index = index_repository(config.workspace, files)
    return {
        "task": task,
        "mode": "evidence_driven_consultant",
        "rules": [
            "The program collects evidence and runs deterministic checks.",
            "The AI is only a consultant; it must not claim execution happened unless evidence shows it.",
            "Prefer tiny exact patches over broad rewrites.",
            "When evidence is insufficient, request missing_evidence instead of guessing.",
        ],
        "repo_map": [{"path": safe_rel(config.workspace, p), "size": p.stat().st_size} for p in files],
        "repository_index": repo_index,
        "selected_files": selected,
        "diagnostics": {"python_compile_errors": compile_python(files, config.workspace), "repository_summary": summarize_index(repo_index)},
    }


def extract_json(raw: str) -> Dict[str, Any]:
    return parse_consultant_json(raw)


def consultant_system_prompt() -> str:
    return (
        "You are Agent Prometheus Consultant. You are not the executor. "
        "The runtime has scanned files, indexed the repository, and run deterministic checks. "
        "Work even when the model is weak: use simple reasoning, short steps, and exact evidence. "
        "Return JSON only with keys: summary, findings, plan, patches, tests_to_run, risks, missing_evidence, confidence. "
        "Patches must be safe exact operations: {op:'replace', path:'relative/path', find:'exact text', replace:'new text'} "
        "or {op:'write_file', path:'relative/path', content:'full file content'}. "
        "Never invent test results. Never mention a file unless it appears in evidence."
    )


def ask_consultant(packet: Dict[str, Any], config: RuntimeConfig, model: Optional[str] = None) -> Dict[str, Any]:
    client = OpenAI(base_url=config.api_base, api_key=config.api_key)
    response = client.chat.completions.create(
        model=model or config.consultant_model,
        temperature=0.1,
        max_tokens=1800,
        messages=[{"role": "system", "content": consultant_system_prompt()}, {"role": "user", "content": json.dumps(packet, ensure_ascii=False)}],
    )
    return extract_json(response.choices[0].message.content or "{}")


def path_allowed(workspace: Path, rel_path: str) -> Path:
    target = (workspace / rel_path).resolve()
    if workspace.resolve() not in target.parents and target != workspace.resolve():
        raise ValueError(f"Refusing to edit outside workspace: {rel_path}")
    if any(part in PROTECTED_PATH_PARTS for part in target.parts):
        raise ValueError(f"Refusing to edit protected path: {rel_path}")
    return target


def apply_patches(patches: List[Dict[str, Any]], config: RuntimeConfig) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for patch in patches[:20]:
        op = patch.get("op")
        rel_path = str(patch.get("path", ""))
        try:
            target = path_allowed(config.workspace, rel_path)
            if op == "replace":
                current = target.read_text(encoding="utf-8", errors="ignore")
                find = str(patch.get("find", ""))
                replace = str(patch.get("replace", ""))
                if not find or find not in current:
                    results.append({"path": rel_path, "applied": False, "reason": "find text not found"})
                    continue
                target.write_text(current.replace(find, replace, 1), encoding="utf-8")
                results.append({"path": rel_path, "applied": True, "op": "replace"})
            elif op == "write_file":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(str(patch.get("content", "")), encoding="utf-8")
                results.append({"path": rel_path, "applied": True, "op": "write_file"})
            else:
                results.append({"path": rel_path, "applied": False, "reason": f"unsupported op {op}"})
        except Exception as exc:
            results.append({"path": rel_path, "applied": False, "reason": str(exc)})
    return results


def render_report(task: str, plan: Dict[str, Any], diagnostics: Dict[str, Any], patch_results: Optional[List[Dict[str, Any]]] = None) -> str:
    return json.dumps({
        "task": task,
        "summary": plan.get("summary"),
        "findings": plan.get("findings", []),
        "plan": plan.get("plan", []),
        "tests_to_run": plan.get("tests_to_run", []),
        "risks": plan.get("risks", []),
        "missing_evidence": plan.get("missing_evidence", []),
        "confidence": plan.get("confidence", "unknown"),
        "diagnostics": diagnostics,
        "patch_results": patch_results or [],
    }, indent=2, ensure_ascii=False)


async def run_task(task: str, chat_id: Optional[int], config: RuntimeConfig, r: redis.Redis) -> str:
    dashboard_log(r, f"Evidence scan started: {task[:160]}", "scanner")
    packet = collect_evidence(task, config)
    dashboard_log(r, f"Evidence packet ready: {len(packet['selected_files'])} files selected", "scanner")
    plan = ask_consultant(packet, config)
    dashboard_log(r, "Consultant plan received", "consultant")

    patch_results: List[Dict[str, Any]] = []
    patches = plan.get("patches") or []
    if patches and config.auto_apply:
        dashboard_log(r, f"Applying {len(patches)} consultant patch operations", "patcher")
        patch_results = apply_patches(patches, config)
        plan["post_patch_diagnostics"] = collect_evidence(task, config).get("diagnostics", {})
    elif patches:
        notify(r, "Approval required before file edits. Consultant proposed patches:\n\n```json\n" + json.dumps(patches[:5], indent=2)[:3500] + "\n```", chat_id=chat_id, approval_gate=False)

    report = render_report(task, plan, packet.get("diagnostics", {}), patch_results)
    notify(r, "Consultant run complete:\n\n```json\n" + report[:3500] + "\n```", chat_id=chat_id)
    return report


async def poll_for_tasks() -> None:
    config = RuntimeConfig()
    r = make_redis(config)
    config.workspace.mkdir(parents=True, exist_ok=True)
    dashboard_log(r, "Agent Prometheus consultant runtime is polling for tasks", "system")
    while True:
        if r.get("prometheus_kill_switch") == "true":
            r.delete("prometheus_kill_switch")
            dashboard_log(r, "Kill switch received. Runtime paused.", "system")
            break
        task_data = r.rpop("prometheus_tasks")
        if task_data:
            try:
                payload = json.loads(task_data)
                task_text = payload.get("task", "").strip()
                if task_text:
                    await run_task(task_text, payload.get("chat_id"), config, r)
            except Exception as exc:
                dashboard_log(r, f"Task failed safely: {exc}", "system")
                notify(r, f"Task failed safely: {exc}")
        await asyncio.sleep(2)


def main() -> None:
    asyncio.run(poll_for_tasks())


if __name__ == "__main__":
    main()
