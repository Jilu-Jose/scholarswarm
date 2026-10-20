import re

import httpx

from .. import config


def parse_handle(value: str) -> str:
    value = (value or "").strip().rstrip("/")
    m = re.search(r"github\.com/([A-Za-z0-9-]+)", value)
    return m.group(1) if m else value.lstrip("@")


async def enrich(handle: str) -> dict:
    """Public GitHub enrichment: repos, languages, stars. Raises on failure so the agent can retry."""
    handle = parse_handle(handle)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ScholarSwarm"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    async with httpx.AsyncClient(timeout=15, headers=headers) as c:
        r = await c.get(f"https://api.github.com/users/{handle}/repos", params={"per_page": 100, "sort": "updated"})
        if r.status_code == 404:
            return {"handle": handle, "found": False, "repos": [], "languages": []}
        r.raise_for_status()
        repos = [x for x in r.json() if not x.get("fork")]
    repos.sort(key=lambda x: (x.get("stargazers_count", 0), x.get("pushed_at", "")), reverse=True)
    langs = {}
    for x in repos:
        if x.get("language"):
            langs[x["language"]] = langs.get(x["language"], 0) + 1
    return {
        "handle": handle,
        "found": True,
        "repos": [{"name": x["name"], "description": x.get("description") or "", "language": x.get("language") or "",
                   "stars": x.get("stargazers_count", 0), "url": x["html_url"], "topics": x.get("topics", [])}
                  for x in repos[:8]],
        "languages": [k for k, _ in sorted(langs.items(), key=lambda kv: -kv[1])][:6],
    }
