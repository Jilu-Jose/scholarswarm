"""Agent 05 - Match Ranker: Multidimensional algorithmic scoring and fit synthesis."""
from ..tools import llm


def score(o: dict, p: dict) -> int:
    s = 50
    for x in o.get("matrix", []):
        lab, st = x["label"], x["status"]
        if lab == "Degree level":
            s += 14 if st == "met" else (-45 if st == "unmet" else 0)
        elif lab == "Academic record":
            s += 10 if st == "met" else -30
        elif lab == "Work experience":
            s += 6 if st == "met" else -25
        elif lab == "Nationality":
            s += 0 if st == "met" else -60
        elif lab == "Field of study":
            s += 8 if st == "met" else -2
        elif lab == "Financial need":
            s += 6 if st == "met" else -15
        elif lab == "English proficiency":
            s += 4 if st == "met" else 0

    if o.get("preferred_destination"):
        s += 14
    need = p.get("funding_need", "full")
    if need == "full":
        s += {"full": 8, "partial": 0}.get(o.get("funding"), -4)
    if o.get("citation", {}).get("ok"):
        s += 8

    margin = p.get("cgpa10", 0) - (o.get("min_cgpa10") or p.get("cgpa10", 0))
    s += max(0, min(margin * 2.5, 8))

    return int(max(1, min(s, 99)))


def _template(o: dict, p: dict) -> str:
    c = o.get("criteria", {})
    met = c.get("met", 0)
    total = c.get("total", 0)
    provider = o.get("provider", "the host institution")
    country = o.get("country", "")

    notes = [f"{met} of {total} checked criteria are met"]
    unmet = [x["label"].lower() for x in o.get("matrix", []) if x["status"] == "unmet"]
    act = [x["label"].lower() for x in o.get("matrix", []) if x["status"] == "action"]

    if unmet:
        notes.append("potential blockers: " + ", ".join(unmet))
    if act:
        notes.append("action items: " + ", ".join(act))

    country_clause = f" for study in {country}" if country and country != "See page" else ""
    return (
        f"Strong alignment with {provider}{country_clause}. "
        f"Your CGPA of {p.get('cgpa10')}/10 clears academic standards; {'; '.join(notes)}."
    )


async def run(run):
    p = run.enriched
    for o in run.candidates:
        o["score"] = score(o, p)
        o["hard_blocked"] = o.get("criteria", {}).get("unmet", 0) > 0

    ranked = sorted(run.candidates, key=lambda o: (o["hard_blocked"], -o["score"]))
    run.ranked = ranked
    run.set("match_ranker", progress=60)

    # Eligible first, fallback to best ranked if none fully eligible
    top = [o for o in ranked if not o["hard_blocked"]][:5] or ranked[:5]
    for o in top:
        o["synthesis"] = _template(o, p)

    if llm.available():
        try:
            payload = [
                {"id": o["id"], "name": o["name"], "matrix": [(x["label"], x["status"], x["detail"]) for x in o.get("matrix", [])]}
                for o in top
            ]
            out = await llm.chat_json(
                "Write an encouraging 2-sentence 'why this fits' note per scholarship for this applicant. Use ONLY the supplied matrix and profile facts. "
                "Schema: {\"<id>\": \"text\"}.",
                f"Candidate: {p.get('name')} (CGPA {p.get('cgpa10')}/10, field '{p.get('field')}'). Programs: {payload}",
                1200
            )
            for o in top:
                if isinstance(out, dict) and out.get(o["id"]):
                    o["synthesis"] = str(out[o["id"]])
            run.log("match_ranker", "LLM synthesized personalized fit rationales for top matches", "ok")
        except Exception as e:  # noqa: BLE001
            run.log("match_ranker", f"LLM notes unavailable ({type(e).__name__}); using rule-grounded notes", "warn")

    for rank, o in enumerate(top, 1):
        o["rank"] = rank
    run.top5 = top

    top_names = [f"#{i} {o['name'][:28]}" for i, o in enumerate(top, 1)]
    run.log("match_ranker", f"Top 5 ranked: {', '.join(top_names)}", "ok")

    if top:
        run.message(
            "match_ranker", "application_writer",
            f"Ranking complete: Selected '{top[0]['name']}' ({top[0]['provider']}) as Top #1 match (Score: {top[0]['score']}%). Commissioning Statement of Purpose draft."
        )


async def fallback(run):
    for o in run.candidates:
        o.setdefault("score", 45)
        o.setdefault("hard_blocked", False)
    run.ranked = sorted(run.candidates, key=lambda o: -o["score"])
    run.top5 = run.ranked[:5]
    for i, o in enumerate(run.top5, 1):
        o["rank"] = i
        o.setdefault("synthesis", "Ranked by fallback criteria.")
    if run.top5:
        run.message("match_ranker", "application_writer", f"Fallback: Top pick is {run.top5[0]['name']}.")
