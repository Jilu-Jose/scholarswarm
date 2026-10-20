"""Thin OpenAI-compatible chat client. Every agent has a deterministic fallback, so the
swarm still works (in 'rules-only' mode) when no key is configured or the API is down."""
import json
import re

import httpx

from .. import config


class LLMUnavailable(Exception):
    pass


def available() -> bool:
    return bool(config.LLM_API_KEY)


async def chat(system: str, user: str, max_tokens: int = 2000, temperature: float = 0.2) -> str:
    if not available():
        raise LLMUnavailable("LLM_API_KEY not configured in backend/.env")
    payload = {
        "model": config.LLM_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    last_err = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(f"{config.LLM_BASE_URL}/chat/completions", json=payload, headers=headers)
                if r.status_code == 401:
                    raise LLMUnavailable("Invalid LLM API key. Check LLM_API_KEY in backend/.env")
                if r.status_code == 404:
                    raise LLMUnavailable(f"Model '{config.LLM_MODEL}' not found at {config.LLM_BASE_URL}")
                if r.status_code in (429, 500, 502, 503):
                    raise httpx.HTTPError(f"HTTP {r.status_code}: {r.text[:120]}")
                r.raise_for_status()
                data = r.json()
                raw_text = data["choices"][0]["message"]["content"] or ""
                # Strip reasoning <think>...</think> tags if emitted by MoE/reasoning models (e.g. gpt-oss-120b)
                cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw_text).strip()
                return cleaned or raw_text.strip()
        except LLMUnavailable:
            raise
        except Exception as e:  # noqa: BLE001
            last_err = e
            import asyncio
            await asyncio.sleep(1.0 * (attempt + 1))
    raise LLMUnavailable(f"LLM call failed after 3 attempts: {last_err!r}")


def _extract_json(text: str):
    clean = text.strip()
    # Try parsing directly
    try:
        return json.loads(clean)
    except Exception:
        pass
    # Strip markdown code blocks
    m_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
    if m_block:
        try:
            return json.loads(m_block.group(1).strip())
        except Exception:
            pass
    # Extract outermost JSON object or array
    m_json = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", clean)
    if m_json:
        try:
            return json.loads(m_json.group(1).strip())
        except Exception:
            pass
    raise ValueError(f"Could not parse valid JSON from LLM response: {text[:200]}")


async def chat_json(system: str, user: str, max_tokens: int = 2000):
    out = await chat(system + "\nReturn ONLY valid JSON. No prose, no conversation, no markdown formatting outside JSON.", user, max_tokens, 0.0)
    return _extract_json(out)

