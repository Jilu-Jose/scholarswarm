"""Agent 02 - Opportunity Scout: dynamic multi-vector live web discovery + verified registry."""
import json
import re

from .. import config
from ..tools import web


def _registry() -> list:
    path = config.DATA_DIR / "opportunities.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))["opportunities"]
        except Exception:
            pass
    return []


def _queries(p: dict) -> list:
    """Build multi-angle search queries tailored to candidate's destination, field, and level."""
    lvl = "master's" if p.get("target_degree") == "masters" else "PhD"
    nat = p.get("nationality") or "international"
    field = p.get("field") or "graduate"
    dests = p.get("destinations") or ["Europe", "Canada", "Singapore"]

    qs = []
    for d in dests[:3]:
        qs.append(f"fully funded {lvl} scholarship {d} {nat} students {field} official")
        qs.append(f"government scholarship {d} {lvl} {field} portal official")

    if p.get("research_interest"):
        qs.append(f"{lvl} research scholarship {p['research_interest']} {dests[0]} official")

    return qs[:5]


def _infer_country(title: str, snippet: str, dests: list) -> str:
    combined = (title + " " + snippet).lower()
    for d in dests:
        if d.lower() in combined:
            return d
    common_countries = [
        "Germany", "United Kingdom", "Canada", "United States", "Singapore",
        "France", "Netherlands", "Japan", "South Korea", "Sweden", "Switzerland", "Hungary", "Australia"
    ]
    for c in common_countries:
        if c.lower() in combined:
            return c
    return dests[0] if dests else "International"


async def run(run):
    p = run.enriched
    cands = []
    for o in _registry():
        cand = dict(o)
        cand["origin"] = "registry"
        cands.append(cand)

    run.log("opportunity_scout", f"Loaded {len(cands)} verified programmes from registry foundation", "ok")
    run.set("opportunity_scout", progress=25)

    known_urls = {o["url"].rstrip("/") for o in cands}
    found_live = 0
    queries = _queries(p)

    for i, q in enumerate(queries):
        run.log("opportunity_scout", f'Live web search [{i + 1}/{len(queries)}]: "{q[:75]}"')
        hits = await web.web_search(q, n=6)
        if not hits:
            continue

        for h in hits:
            u = h["url"].rstrip("/")
            if u in known_urls:
                continue
            known_urls.add(u)
            found_live += 1

            host_name = web.host(u)
            inferred_country = _infer_country(h["title"], h["snippet"], p.get("destinations", []))
            clean_title = re.sub(r"\s*[-|–—]\s*.*$", "", h["title"]).strip() or h["title"][:80]

            cands.append({
                "id": f"web-{len(cands) + 1}",
                "name": clean_title,
                "provider": host_name,
                "country": inferred_country,
                "levels": [p.get("target_degree", "masters")],
                "funding": "full" if "fully" in h["snippet"].lower() else "unknown",
                "funding_summary": h["snippet"][:250],
                "url": h["url"],
                "fallback_urls": [],
                "fields": [p.get("field", "any")],
                "origin": "web-discovery",
                "how_to_apply": "Visit the official portal to review application procedures.",
            })
        run.set("opportunity_scout", progress=25 + int((i + 1) / len(queries) * 65))

    dest_set = {d.lower() for d in p.get("destinations", [])}
    for o in cands:
        o["preferred_destination"] = (
            o.get("country", "").lower() in dest_set
            or any(d in o.get("country", "").lower() for d in dest_set)
        )

    run.candidates = cands
    run.log(
        "opportunity_scout",
        f"Discovery phase complete: {len(cands)} candidate opportunities queued ({found_live} from live web)",
        "ok"
    )
    run.message(
        "opportunity_scout", "source_critic",
        f"Found {len(cands)} total candidate programmes ({found_live} live web discoveries). Submitting to Source Critic for domain auditing."
    )


async def fallback(run):
    p = run.enriched
    run.candidates = [dict(o, origin="registry") for o in _registry()]
    dest_set = {d.lower() for d in p.get("destinations", [])}
    for o in run.candidates:
        o["preferred_destination"] = o.get("country", "").lower() in dest_set
    run.log("opportunity_scout", "Fallback: using registry candidates only", "warn")
    run.message("opportunity_scout", "source_critic", f"Fallback: passed {len(run.candidates)} registry candidates.")
