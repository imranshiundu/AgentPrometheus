from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Iterable

import redis

FEATURE_MODES = {"off", "auto", "on"}
FEATURE_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "telegram": {
        "label": "Telegram Gateway",
        "default_mode": os.getenv("PROMETHEUS_FEATURE_TELEGRAM", "off"),
        "description": "Mobile task intake, approval buttons, and runtime notifications.",
        "ram": "low-medium",
    },
    "memory": {
        "label": "Chroma Memory",
        "default_mode": os.getenv("PROMETHEUS_FEATURE_MEMORY", "auto"),
        "description": "Persistent vector memory and long-running lesson store.",
        "ram": "medium-heavy",
    },
    "router": {
        "label": "LiteLLM Router",
        "default_mode": os.getenv("PROMETHEUS_FEATURE_ROUTER", "auto"),
        "description": "Multi-provider model routing and model aliases.",
        "ram": "medium",
    },
    "vision": {
        "label": "Vision Bridge",
        "default_mode": os.getenv("PROMETHEUS_FEATURE_VISION", "off"),
        "description": "Optional paired local observation/context bridge.",
        "ram": "medium",
    },
    "openhands": {
        "label": "OpenHands Sandbox",
        "default_mode": os.getenv("PROMETHEUS_FEATURE_OPENHANDS", "off"),
        "description": "Heavy external developer sandbox service.",
        "ram": "heavy",
    },
    "deep_scan": {
        "label": "Deep Scan",
        "default_mode": os.getenv("PROMETHEUS_FEATURE_DEEP_SCAN", "auto"),
        "description": "Larger repository evidence budget for deep inspections.",
        "ram": "cpu/token-heavy",
    },
    "voice": {
        "label": "Voice Transcription",
        "default_mode": os.getenv("PROMETHEUS_FEATURE_VOICE", "off"),
        "description": "Telegram voice-note transcription.",
        "ram": "api-cost",
    },
}
FEATURE_KEY_PREFIX = os.getenv("PROMETHEUS_FEATURE_KEY_PREFIX", "prometheus_feature")


def utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def normalize_mode(mode: str | None, fallback: str = "off") -> str:
    value = (mode or fallback or "off").strip().lower()
    return value if value in FEATURE_MODES else fallback


def feature_mode_key(name: str) -> str:
    return f"{FEATURE_KEY_PREFIX}:{name}:mode"


def feature_state_key(name: str) -> str:
    return f"{FEATURE_KEY_PREFIX}:{name}:state"


def feature_request_key(name: str) -> str:
    return f"{FEATURE_KEY_PREFIX}:{name}:request"


def list_feature_names() -> list[str]:
    return sorted(FEATURE_DEFINITIONS.keys())


def feature_default_mode(name: str) -> str:
    definition = FEATURE_DEFINITIONS.get(name, {})
    return normalize_mode(definition.get("default_mode"), "off")


def safe_redis(func, default: Any = None) -> Any:
    try:
        return func()
    except redis.RedisError:
        return default


def read_feature(r: redis.Redis, name: str) -> Dict[str, Any]:
    if name not in FEATURE_DEFINITIONS:
        raise KeyError(name)
    definition = FEATURE_DEFINITIONS[name]
    mode = normalize_mode(safe_redis(lambda: r.get(feature_mode_key(name)), None), feature_default_mode(name))
    state = safe_redis(lambda: r.get(feature_state_key(name)), "idle") or "idle"
    request = safe_redis(lambda: r.get(feature_request_key(name)), None)
    return {
        "name": name,
        "label": definition["label"],
        "description": definition["description"],
        "ram": definition["ram"],
        "mode": mode,
        "state": state,
        "requested": bool(request),
        "request_reason": request,
        "active": mode == "on" or (mode == "auto" and bool(request)),
    }


def list_features(r: redis.Redis) -> list[Dict[str, Any]]:
    return [read_feature(r, name) for name in list_feature_names()]


def set_feature_mode(r: redis.Redis, name: str, mode: str) -> Dict[str, Any]:
    if name not in FEATURE_DEFINITIONS:
        raise KeyError(name)
    normalized = normalize_mode(mode, "off")
    safe_redis(lambda: r.set(feature_mode_key(name), normalized))
    safe_redis(lambda: r.set(feature_state_key(name), f"mode:{normalized}@{utc_now()}"))
    if normalized == "off":
        safe_redis(lambda: r.delete(feature_request_key(name)))
    return read_feature(r, name)


def request_feature(r: redis.Redis, name: str, reason: str) -> Dict[str, Any]:
    if name not in FEATURE_DEFINITIONS:
        raise KeyError(name)
    mode = normalize_mode(safe_redis(lambda: r.get(feature_mode_key(name)), None), feature_default_mode(name))
    if mode == "off":
        safe_redis(lambda: r.set(feature_state_key(name), f"blocked:{reason[:160]}@{utc_now()}"))
        return read_feature(r, name)
    safe_redis(lambda: r.set(feature_request_key(name), reason[:240]))
    safe_redis(lambda: r.set(feature_state_key(name), f"requested@{utc_now()}"))
    return read_feature(r, name)


def clear_feature_request(r: redis.Redis, name: str) -> Dict[str, Any]:
    if name not in FEATURE_DEFINITIONS:
        raise KeyError(name)
    safe_redis(lambda: r.delete(feature_request_key(name)))
    safe_redis(lambda: r.set(feature_state_key(name), f"idle@{utc_now()}"))
    return read_feature(r, name)


def feature_active(r: redis.Redis, name: str) -> bool:
    try:
        return bool(read_feature(r, name).get("active"))
    except KeyError:
        return False


def infer_needed_features(task: str) -> list[tuple[str, str]]:
    text = task.lower()
    needs: list[tuple[str, str]] = []
    keyword_map: Iterable[tuple[str, tuple[str, ...], str]] = [
        ("memory", ("remember", "memory", "previous", "history", "learn from", "long term"), "task asks for persistent memory or previous context"),
        ("router", ("claude", "gemini", "openrouter", "fallback model", "model route", "provider"), "task mentions model routing/provider selection"),
        ("vision", ("screen", "screenshot", "observe", "vision", "desktop", "camera"), "task asks for visual/local observation context"),
        ("telegram", ("telegram", "phone", "mobile", "notify me", "message me"), "task asks for Telegram/mobile notification"),
        ("openhands", ("openhands", "sandbox", "browser automation", "run in sandbox"), "task asks for heavy sandbox automation"),
        ("deep_scan", ("scan all", "entire repo", "all files", "code by code", "deep scan", "everything"), "task asks for a broad/deep repository scan"),
        ("voice", ("voice", "audio", "transcribe", "voice note"), "task asks for voice transcription"),
    ]
    for name, keywords, reason in keyword_map:
        if any(keyword in text for keyword in keywords):
            needs.append((name, reason))
    return needs
