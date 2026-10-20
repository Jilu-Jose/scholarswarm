"""Agent 04 - Eligibility Verifier: Live official page crawler, criteria extractor, and rule engine."""
import asyncio
import time

from .. import config, rules
from ..tools import llm, parsing, web


async def _fetch_with_recovery(run, o):
    """Primary URL -> official mirror fallbacks -> web.archive.org snapshot."""
    if not config.LIVE_FETCH:
        return await web.fetch_page(o["url"]), o["url"], False
    tried = [o["url"]] + list(o.get("fallback_urls", []))
    page = {"ok": False, "status": 0, "error": "not attempted"}
    for i, u in enumerate(tried):
        page = await web.fetch_page(u)
        if page["ok"]:
            if i > 0:
                run.stats["retries"] += 1
                run.log("eligibility_verifier", f"Recovered {o['name'][:40]} via official fallback {web.host(u)}", "warn")
            return page, u, i > 0
        run.log("eligibility_verifier", f"{web.host(u)} -> {page.get('error') or page.get('status')}; trying alternate route", "warn")
    snap = await web.fetch_page("https://web.archive.org/web/2/" + o["url"], retries=0)
    if snap["ok"]:
        run.stats["retries"] += 1
        run.log("eligibility_verifier", f"Used archived snapshot for {o['name'][:40]} (label: archived)", "warn")
        snap["archived"] = True
        return snap, o["url"], True
    return page, o["url"], False


async def _llm_extract(o, text):
    try:
        d = await llm.chat_json(
            "Extract structured criteria for this scholarship from the official page text. Use ONLY facts directly stated in the text. "
            'Schema: {"deadline": str|null, "funding_summary": str|null, "is_fully_funded": bool|null, "requirements": [str], "min_ielts": float|null, "min_work_years": int|null}. '
            "requirements: up to 4 concise concrete items.",
            f"Programme: {o['name']} ({o.get('provider')})\nPAGE TEXT:\n{text[:9500]}", 750
        )
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


async def run(run):
    p = run.enriched
    sem = asyncio.Semaphore(config.MAX_CONCURRENCY)
    total = len(run.candidates)
    done = 0

    async def work(o):
        nonlocal done
        async with sem:
            page, used, fb = await _fetch_with_recovery(run, o)
            cit = {
                "ok": page["ok"], "status": page["status"], "used_url": used,
                "final_url": page.get("final_url", used), "sha256": page.get("sha256", ""),
                "fetched_at": page["fetched_at"], "fallback_used": fb,
                "archived": bool(page.get("archived")), "error": page.get("error", ""),
                "official": web.is_official(o["url"]), "title": page.get("title", "")
            }
            o["citation"] = cit
            text = page.get("text", "")

            # 1. Deadlines
            snippets = web.find_deadlines(text) if text else []
            o["deadline_snippets"] = snippets
            o["deadline_text"] = snippets[0] if snippets else ""

            # 2. Extract criteria from text
            o["page_requirements"] = []
            extracted_from_llm = False

            if text and llm.available():
                ext = await _llm_extract(o, text)
                if ext:
                    extracted_from_llm = True
                    if ext.get("deadline"):
                        o["deadline_text"] = str(ext["deadline"])
                        o["deadline_source"] = "llm-extract-from-page"
                    if ext.get("requirements"):
                        o["page_requirements"] = [str(x) for x in ext["requirements"]][:4]
                    if ext.get("funding_summary"):
                        o["funding_summary"] = str(ext["funding_summary"])[:250]
                    if ext.get("is_fully_funded") is True:
                        o["funding"] = "full"
                    if ext.get("min_ielts") is not None:
                        o["ielts_min"] = float(ext["min_ielts"])
                    if ext.get("min_work_years") is not None:
                        o["min_work_years"] = int(ext["min_work_years"])

            # Fallback heuristic extraction if LLM didn't run or missed items
            if text and not extracted_from_llm:
                reqs = parsing.extract_requirements(text)
                if reqs:
                    o["page_requirements"] = reqs
                ftype, fsum = parsing.extract_funding_type(text)
                if ftype != "unknown" and o.get("origin") == "web-discovery":
                    o["funding"] = ftype
                    o["funding_summary"] = fsum
                extracted_levels = parsing.extract_degree_levels(text)
                if extracted_levels and not o.get("levels"):
                    o["levels"] = extracted_levels
                ie = parsing.extract_ielts_requirement(text)
                if ie is not None and not o.get("ielts_min"):
                    o["ielts_min"] = ie
                wy = parsing.extract_work_years_requirement(text)
                if wy > 0 and not o.get("min_work_years"):
                    o["min_work_years"] = wy

            # 3. Deterministic rule engine evaluation
            o["matrix"] = rules.check(o, p)
            o["criteria"] = rules.summarise(o["matrix"])
            if not cit["ok"]:
                o["matrix"].append({
                    "label": "Official page check", "status": "unknown",
                    "detail": "Could not connect to portal live; evaluated from registry specifications"
                })

            done += 1
            if page["ok"] and (done % 4 == 0 or done == total):
                run.log(
                    "eligibility_verifier",
                    f"Crawled & verified {done}/{total} official pages (latest: {web.host(o['url'])} HTTP {page['status']})",
                    "ok"
                )
            run.set("eligibility_verifier", progress=int(done / max(total, 1) * 95))

    run.log("eligibility_verifier", f"Initiating live crawl of {total} official portals ({config.MAX_CONCURRENCY} parallel workers)")
    await asyncio.gather(*(work(o) for o in run.candidates))

    ok_count = sum(1 for o in run.candidates if o.get("citation", {}).get("ok"))
    run.log(
        "eligibility_verifier",
        f"Verification complete: {ok_count}/{total} official portals reachable and content-hashed",
        "ok" if ok_count else "warn"
    )
    run.message(
        "eligibility_verifier", "match_ranker",
        f"Verification completed for {total} official portals ({ok_count} live-hashed). Handing verified criteria to Match Ranker."
    )


async def fallback(run):
    for o in run.candidates:
        o.setdefault("citation", {
            "ok": False, "status": 0, "used_url": o["url"], "final_url": o["url"], "sha256": "",
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "fallback_used": False, "archived": False, "error": "offline fallback",
            "official": web.is_official(o["url"]), "title": ""
        })
        o.setdefault("deadline_text", "")
        o.setdefault("deadline_snippets", [])
        o.setdefault("page_requirements", [])
        o["matrix"] = rules.check(o, run.enriched)
        o["criteria"] = rules.summarise(o["matrix"])
    run.log("eligibility_verifier", "Fallback: criteria evaluated from registry baseline only", "warn")
    run.message("eligibility_verifier", "match_ranker", "Fallback: evaluated candidates from registry baseline.")
