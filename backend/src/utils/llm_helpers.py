"""
Helpers for parsing LLM responses.
"""

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        if len(parts) >= 2:
            cleaned = parts[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
    return cleaned.strip()


def parse_json_response(text: str, default: Optional[Any] = None) -> Any:
    """
    Parse JSON content from an LLM response.

    Handles raw JSON, fenced JSON blocks, and embedded JSON objects/arrays.
    """
    if text is None:
        return default

    cleaned = _strip_code_fences(text)

    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

    logger.warning("Failed to parse JSON from LLM response")
    return default
