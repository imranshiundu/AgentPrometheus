from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

LANGUAGE_BY_SUFFIX = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".json": "JSON", ".md": "Markdown", ".yml": "YAML",
    ".yaml": "YAML", ".toml": "TOML", ".ini": "INI", ".css": "CSS",
    ".html": "HTML", ".sh": "Shell", ".dockerfile": "Dockerfile",
}
ENTRYPOINT_NAMES = {
    "main.py", "app.py", "server.py", "manage.py", "index.js", "server.js", "app.js",
    "main.ts", "index.ts", "Dockerfile", "docker-compose.yml", "compose.yml",
    "package.json", "pyproject.toml", "requirements.txt",
}
FASTAPI_ROUTE_RE = re.compile(r"@(?:app|router)\.(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)")
REDIS_RE = re.compile(r"\b(redis|Redis|prometheus_tasks|prometheus_logs|prometheus_notifications)\b")
ENV_RE = re.compile(r"os\.getenv\(['\"]([^'\"]+)['\"]")
IMPORT_RE = re.compile(r"^(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))", re.MULTILINE)


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def detect_language(path: Path) -> str:
    if path.name == "Dockerfile" or path.name.endswith(".Dockerfile"):
        return "Dockerfile"
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "Text")


def safe_read(path: Path, max_chars: int = 20000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def parse_python_symbols(text: str) -> Dict[str, List[str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"classes": [], "functions": [], "imports": []}
    classes: List[str] = []
    functions: List[str] = []
    imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    return {"classes": sorted(set(classes))[:40], "functions": sorted(set(functions))[:80], "imports": sorted(set(imports))[:80]}


def parse_package_json(text: str) -> Dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    deps = sorted({**data.get("dependencies", {}), **data.get("devDependencies", {})}.keys())[:120]
    return {"package_name": data.get("name"), "scripts": sorted((data.get("scripts") or {}).keys())[:60], "dependencies": deps}


def index_repository(workspace: Path, files: Iterable[Path]) -> Dict[str, Any]:
    file_list = list(files)
    languages = Counter(detect_language(path) for path in file_list)
    directories = Counter(relpath(workspace, path.parent).split("/")[0] for path in file_list)
    entrypoints: List[str] = []
    docker_files: List[str] = []
    compose_files: List[str] = []
    fastapi_routes: List[Dict[str, str]] = []
    redis_touchpoints: List[str] = []
    env_vars = set()
    imports_by_file: Dict[str, List[str]] = {}
    python_symbols: Dict[str, Dict[str, List[str]]] = {}
    package_manifests: List[Dict[str, Any]] = []
    dependency_files: List[str] = []

    for path in file_list:
        rel = relpath(workspace, path)
        lower_name = path.name.lower()
        if path.name in ENTRYPOINT_NAMES or lower_name.endswith(".dockerfile"):
            entrypoints.append(rel)
        if path.name == "Dockerfile" or lower_name.endswith(".dockerfile"):
            docker_files.append(rel)
        if path.name in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
            compose_files.append(rel)
        if path.name in {"requirements.txt", "pyproject.toml", "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"}:
            dependency_files.append(rel)
        text = safe_read(path)
        if not text:
            continue
        for match in FASTAPI_ROUTE_RE.finditer(text):
            fastapi_routes.append({"file": rel, "method": match.group(1).upper(), "path": match.group(2)})
        if REDIS_RE.search(text):
            redis_touchpoints.append(rel)
        env_vars.update(ENV_RE.findall(text))
        if path.suffix == ".py":
            symbols = parse_python_symbols(text)
            python_symbols[rel] = symbols
            imports_by_file[rel] = symbols.get("imports", [])
        else:
            imports = sorted(set((a or b).split(".")[0] for a, b in IMPORT_RE.findall(text)))[:60]
            if imports:
                imports_by_file[rel] = imports
        if path.name == "package.json":
            parsed = parse_package_json(text)
            if parsed:
                parsed["file"] = rel
                package_manifests.append(parsed)
    return {
        "file_count": len(file_list), "languages": dict(languages.most_common()),
        "top_directories": dict(directories.most_common(20)), "entrypoints": sorted(set(entrypoints))[:80],
        "dependency_files": sorted(set(dependency_files))[:40], "docker_files": sorted(set(docker_files))[:40],
        "compose_files": sorted(set(compose_files))[:20], "fastapi_routes": fastapi_routes[:120],
        "redis_touchpoints": sorted(set(redis_touchpoints))[:80], "environment_variables": sorted(env_vars)[:120],
        "imports_by_file": imports_by_file, "python_symbols": python_symbols, "package_manifests": package_manifests,
    }


def summarize_index(index: Dict[str, Any]) -> str:
    return "\n".join([
        f"Files indexed: {index.get('file_count', 0)}",
        f"Languages: {index.get('languages', {})}",
        f"Entrypoints: {', '.join(index.get('entrypoints', [])[:12]) or 'none detected'}",
        f"Dependency files: {', '.join(index.get('dependency_files', [])[:12]) or 'none detected'}",
        f"Docker files: {', '.join(index.get('docker_files', [])[:12]) or 'none detected'}",
        f"FastAPI routes: {len(index.get('fastapi_routes', []))}",
        f"Redis touchpoints: {', '.join(index.get('redis_touchpoints', [])[:12]) or 'none detected'}",
    ])
