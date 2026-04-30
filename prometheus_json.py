from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable

EXPECTED_KEYS = {
    "summary": "",
    "findings": [],
    "plan": [],
    "patches": [],
    "tests_to_run": [],
    "risks": [],
    "missing_evidence": [],
    "confidence": "low",
}


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _quote_unquoted_keys(text: str) -> str:
    return re.sub(r"([,{]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', text)


def _normalise_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_consultant_response(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(EXPECTED_KEYS)
    normalized.update(data if isinstance(data, dict) else {})
    normalized["summary"] = str(normalized.get("summary") or "")
    normalized["findings"] = _normalise_list(normalized.get("findings"))
    normalized["plan"] = _normalise_list(normalized.get("plan"))
    normalized["patches"] = _normalise_list(normalized.get("patches"))
    normalized["tests_to_run"] = _normalise_list(normalized.get("tests_to_run"))
    normalized["risks"] = _normalise_list(normalized.get("risks"))
    normalized["missing_evidence"] = _normalise_list(normalized.get("missing_evidence"))
    confidence = str(normalized.get("confidence") or "low").lower()
    normalized["confidence"] = confidence if confidence in {"low", "medium", "high"} else "low"
    normalized["patches"] = [p for p in normalized["patches"] if isinstance(p, dict)]
    return normalized


def parse_consultant_json(raw: str) -> Dict[str, Any]:
    text = _extract_object(_strip_code_fence(raw or ""))
    attempts: Iterable[str] = (
        text,
        _remove_trailing_commas(text),
        _quote_unquoted_keys(_remove_trailing_commas(text)),
    )
    for candidate in attempts:
        try:
            return normalize_consultant_response(json.loads(candidate))
        except json.JSONDecodeError:
            continue
    return normalize_consultant_response(
        {
            "summary": (raw or "")[:2000],
            "confidence": "low",
            "missing_evidence": ["Model did not return valid JSON after repair attempts."],
            "patches": [],
        }
    )
