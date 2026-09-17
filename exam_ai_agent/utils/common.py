"""
Shared utility functions for LLM invocation, JSON extraction, and concurrent URL validation.
"""

import re
import json
import time
import urllib3
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

# Suppress insecure request warnings for fallback SSL-tolerant requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_logger(__name__)


def get_llm(
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
):
    """
    Return a ChatGoogleGenerativeAI instance using settings configuration,
    or None if no API key is available.
    """
    api_key = settings.resolve_gemini_key()
    if not api_key:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=api_key,
            temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
            timeout=timeout or settings.LLM_TIMEOUT,
        )
    except Exception as e:
        logger.error("Failed to initialize ChatGoogleGenerativeAI: %s", e)
        return None


def strip_json_fences(text: str) -> str:
    """
    Remove markdown code fences (```json ... ```) from LLM output.
    Extracts the first valid JSON array or object substring if surrounded by extra text.
    """
    if not text:
        return ""
    cleaned = text.strip()
    # Remove leading ```json or ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    # Remove trailing ```
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # Extract JSON object or array if extra prose wraps it
    brace_start = cleaned.find("{")
    bracket_start = cleaned.find("[")

    if bracket_start != -1 and (brace_start == -1 or bracket_start < brace_start):
        bracket_end = cleaned.rfind("]")
        if bracket_end > bracket_start:
            return cleaned[bracket_start : bracket_end + 1].strip()

    if brace_start != -1:
        brace_end = cleaned.rfind("}")
        if brace_end > brace_start:
            return cleaned[brace_start : brace_end + 1].strip()

    return cleaned


def invoke_llm_with_retry(
    llm,
    messages: list,
    retries: int = 3,
    base_delay: float = 3.0,
) -> Optional[str]:
    """
    Invoke LLM with exponential backoff on 429 RESOURCE_EXHAUSTED or transient errors.
    Returns response content string, or None on failure.
    """
    if not llm:
        return None

    delay = base_delay
    for attempt in range(retries):
        try:
            res = llm.invoke(messages)
            return res.content if hasattr(res, "content") else str(res)
        except Exception as e:
            err_str = str(e)
            is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
            is_transient = "503" in err_str or "500" in err_str or "timeout" in err_str.lower()

            if (is_quota or is_transient) and attempt < retries - 1:
                logger.warning(
                    "LLM call encountered transient issue (%s). Retrying %d/%d in %.1fs...",
                    err_str[:80],
                    attempt + 1,
                    retries,
                    delay,
                )
                time.sleep(delay)
                delay *= 2
            else:
                logger.error("LLM invocation failed permanently: %s", e)
                break
    return None


def check_url_alive(
    url: str,
    timeout: int = 5,
    user_agent: Optional[str] = None,
) -> bool:
    """
    Check if a URL returns a valid non-error HTTP status.
    Uses browser headers and fallback SSL handling for government portals.
    """
    if not url or not url.startswith(("http://", "https://")):
        return False

    headers = {
        "User-Agent": user_agent or settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        # First try lightweight HEAD request
        resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code < 400:
            return True
        # If server rejects HEAD (common: 403/405), try GET with stream=True
        if resp.status_code in (403, 405, 400):
            resp = requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)
            return resp.status_code < 400
        return False
    except requests.exceptions.SSLError:
        # Retry with verify=False for government sites with misconfigured/expired SSL chains
        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                stream=True,
                verify=False,
                allow_redirects=True,
            )
            return resp.status_code < 400
        except Exception:
            return False
    except Exception:
        return False


def filter_alive_urls_concurrent(
    items: List[Any],
    max_workers: int = 8,
    timeout: int = 5,
) -> List[Any]:
    """
    Filter a list of URL strings or dicts with a 'url' key concurrently.
    Preserves original list order and skips dead links in parallel.
    """
    if not items:
        return []

    # Map item to URL string
    def _extract_url(item: Any) -> str:
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return item.get("url") or item.get("href") or item.get("link") or ""
        return getattr(item, "url", "")

    extracted = [(_extract_url(item), i, item) for i, item in enumerate(items)]
    valid_candidates = [(u, i, item) for (u, i, item) in extracted if u]

    if not valid_candidates:
        return []

    alive_indices = set()
    worker_count = min(len(valid_candidates), max_workers)

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(check_url_alive, u, timeout): i
            for (u, i, _) in valid_candidates
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                if future.result():
                    alive_indices.add(idx)
            except Exception:
                pass

    return [item for i, item in enumerate(items) if i in alive_indices]
