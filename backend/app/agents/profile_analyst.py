"""Agent 01 - Profile Analyst: resume + transcript + GitHub + extra URLs -> enriched profile."""
import asyncio

from .. import rules
from ..tools import github, llm, parsing, web


def _strengths_rules(p: dict, repos: list, skills: list) -> list:
    s = []
    if rules.cgpa10(p) >= 8.0:
        g = rules.bavarian(p)
        s.append({"title": "Strong academic standing", "detail": f"CGPA {p['cgpa']}/{p['cgpa_scale']:g}" + (f" (~{g} on the German scale, approx.)" if g else "")})
    elif rules.cgpa10(p) >= 7.0:
        s.append({"title": "Solid academic record", "detail": f"CGPA {p['cgpa']}/{p['cgpa_scale']:g} clears most funded-programme minimums"})
    if repos:
        top = repos[0]
        s.append({"title": "Public project evidence", "detail": f"{len(repos)} public repos; top: {top['name']} ({top['language'] or 'n/a'}, {top['stars']} stars)"})
    elif parsing.extract_projects(p.get("resume_text", "")):
        s.append({"title": "Documented projects", "detail": f"{len(parsing.extract_projects(p['resume_text']))} projects listed on the resume"})
    if skills:
        s.append({"title": "Technical breadth", "detail": ", ".join(skills[:6])})
    return s[:3]


async def _gather(run):
    p = run.profile.model_dump()
    text = (p["resume_text"] or "") + "\n" + (p["transcript_text"] or "")
    run.log("profile_analyst", f"Parsing resume and transcript ({len(text)} chars)")
    run.set("profile_analyst", progress=15)

    if not p.get("cgpa"):
        d = parsing.detect_cgpa(text)
        if d:
            p["cgpa"], p["cgpa_scale"] = d
    skills = set(p["skills"]) | set(parsing.extract_skills(text))

    repos, gh = [], {}
    if p["github"]:
        run.log("profile_analyst", f"Querying GitHub API for {github.parse_handle(p['github'])}")
        last = None
        for i in range(3):
            try:
                gh = await github.enrich(p["github"])
                break
            except Exception as e:  # noqa: BLE001
                last = e
                run.log("profile_analyst", f"GitHub attempt {i + 1} failed ({type(e).__name__}); retrying", "warn")
                await asyncio.sleep(1 + i)
        else:
            run.log("profile_analyst", f"GitHub unreachable ({last!r}); continuing with resume only", "warn")
        if gh.get("found"):
            repos = gh["repos"]
            skills |= set(gh["languages"])
            run.log("profile_analyst", f"GitHub: {len(repos)} original repos, languages {', '.join(gh['languages'][:4])}", "ok")
        elif gh:
            run.log("profile_analyst", "GitHub handle not found; skipping", "warn")
    else:
        run.log("profile_analyst", "No GitHub supplied; resume is the only technical evidence", "warn")
    run.set("profile_analyst", progress=55)

    extra = []
    for u in p["extra_urls"][:3]:
        pg = await web.fetch_page(u, retries=1)
        if pg["ok"]:
            found = parsing.extract_skills(pg["text"])
            skills |= set(found)
            extra.append({"url": u, "title": pg["title"], "skills": found[:8]})
            run.log("profile_analyst", f"Read supplied profile {web.host(u)}: +{len(found)} skills", "ok")
        else:
            run.log("profile_analyst", f"Could not read {u}: {pg['error']}", "warn")
    run.set("profile_analyst", progress=75)

    p["skills"] = sorted(skills)
    p["repos"] = repos
    p["extra_profiles"] = extra
    p["projects"] = parsing.extract_projects(p["resume_text"])
    p["bavarian"] = rules.bavarian(p)
    p["cgpa10"] = rules.cgpa10(p)
    return p, repos


def _score(p, repos) -> int:
    s = min(p["cgpa10"] / 10 * 45, 45) + min(len(p["skills"]), 10) * 2.5
    s += 10 if repos else (4 if p["projects"] else 0)
    s += 5 if p["resume_text"] else 0
    s += 5 if p["transcript_text"] else 0
    return int(min(s, 99))


async def run(run):
    p, repos = await _gather(run)
    strengths = None
    if llm.available() and (p["resume_text"] or repos):
        try:
            ctx = f"Resume:\n{p['resume_text'][:3500]}\nRepos: {[(r['name'], r['description']) for r in repos[:6]]}\nCGPA {p['cgpa']}/{p['cgpa_scale']}"
            strengths = await llm.chat_json(
                "Extract up to 3 evidence-backed strengths for a scholarship application. Use ONLY facts in the input. "
                "Schema: [{\"title\": str, \"detail\": str}]. Each detail must be under 22 words.", ctx, 700)
            strengths = [s for s in strengths if isinstance(s, dict) and "title" in s][:3]
            run.log("profile_analyst", "LLM extracted strengths from resume evidence", "ok")
        except Exception as e:  # noqa: BLE001
            run.log("profile_analyst", f"LLM strengths unavailable ({type(e).__name__}); using rule-based strengths", "warn")
    p["strengths"] = strengths or _strengths_rules(p, repos, p["skills"])
    p["profile_score"] = _score(p, repos)
    run.enriched = p
    run.briefing = {
        "name": p["name"], "degree": p["degree"], "field": p["field"], "cgpa10": p["cgpa10"],
        "target_degree": p["target_degree"], "destinations": p["destinations"],
        "funding_need": p["funding_need"], "research_interest": p.get("research_interest", ""),
        "skills": p["skills"][:8], "repos": [r["name"] for r in repos[:3]],
    }
    run.events.append({"type": "profile", "data": p})
    run.set("profile_analyst", progress=95)
    run.log("profile_analyst", f"Profile ready: CGPA {p['cgpa10']}/10, {len(p['skills'])} skills, score {p['profile_score']}/100", "ok")
    run.message(
        "profile_analyst", "opportunity_scout",
        f"Briefing: Candidate {p['name'] or 'Student'} ({p['degree']} {p['field']}, CGPA {p['cgpa10']}/10) targeting {p['target_degree']} in {', '.join(p['destinations'])}. Deploying web & registry discovery."
    )



async def fallback(run):
    """Minimal enrichment: use submitted fields only."""
    p = run.profile.model_dump()
    p.update(repos=[], extra_profiles=[], projects=parsing.extract_projects(p["resume_text"]),
             skills=sorted(set(p["skills"]) | set(parsing.extract_skills(p["resume_text"]))),
             cgpa10=rules.cgpa10(p), bavarian=rules.bavarian(p))
    p["strengths"] = _strengths_rules(p, [], p["skills"])
    p["profile_score"] = _score(p, [])
    run.enriched = p
    run.events.append({"type": "profile", "data": p})
    run.log("profile_analyst", "Fallback: profile built from submitted form fields only", "warn")
