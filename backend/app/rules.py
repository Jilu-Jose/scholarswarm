"""Deterministic eligibility rule engine. No LLM involved, so results are reproducible."""


def cgpa10(p: dict) -> float:
    scale = p.get("cgpa_scale") or 10.0
    return round(float(p.get("cgpa") or 0) / scale * 10, 2)


def bavarian(p: dict, nmin: float = 5.0):
    """Approx. German grade via the modified Bavarian formula (Nmin=5 assumed on a 10 scale)."""
    c = cgpa10(p)
    if c < nmin:
        return None
    return round((10 - c) / (10 - nmin) * 3 + 1, 1)


def check(opp: dict, p: dict) -> list:
    """Return an eligibility matrix: [{label, status(met|unmet|action|unknown), detail}]."""
    m = []

    def add(label, status, detail):
        m.append({"label": label, "status": status, "detail": detail})

    levels = opp.get("levels") or []
    tgt = p.get("target_degree", "masters")
    if levels:
        if tgt in levels:
            add("Degree level", "met", f"Funds {' / '.join(levels)}; you are targeting {tgt}")
        else:
            add("Degree level", "unmet", f"Funds {' / '.join(levels)} only; you are targeting {tgt}")
    else:
        add("Degree level", "unknown", "Level not stated; confirm on the official page")

    nat = opp.get("nationalities", "any")
    if nat == "any" or p.get("nationality", "India") in nat:
        add("Nationality", "met", f"Open to applicants from {p.get('nationality', 'India')} (per registry)")
    else:
        add("Nationality", "unmet", f"Restricted to {', '.join(nat)}")

    req = opp.get("min_cgpa10")
    c = cgpa10(p)
    if req:
        if c >= req:
            add("Academic record", "met", f"CGPA {c}/10 vs indicative minimum {req}")
        else:
            add("Academic record", "unmet", f"CGPA {c}/10 is below the indicative {req}")

    wy = opp.get("min_work_years") or 0
    have = float(p.get("work_years") or 0)
    if wy:
        if have >= wy:
            add("Work experience", "met", f"{have:g} yr vs {wy} yr required")
        else:
            add("Work experience", "unmet", f"Requires about {wy} yr of work experience; you have {have:g}")

    kws = [k.lower() for k in (opp.get("fields") or [])]
    if not kws or "any" in kws:
        add("Field of study", "met", "Open to all fields")
    else:
        blob = " ".join([p.get("field", ""), p.get("research_interest", ""), p.get("degree", "")] + list(p.get("skills", []))).lower()
        if any(k in blob for k in kws):
            add("Field of study", "met", "Your field matches the programme focus")
        else:
            add("Field of study", "unknown", f"Programme focus: {', '.join(kws)}; confirm fit")

    ie = opp.get("ielts_min")
    if ie:
        st, sc = p.get("ielts_status", "none"), p.get("ielts_score")
        if st == "have" and sc is not None:
            if sc >= ie:
                add("English proficiency", "met", f"IELTS {sc} vs ~{ie} typical minimum")
            else:
                add("English proficiency", "action", f"IELTS {sc} is under the ~{ie} typical minimum; retake or check waivers")
        elif st == "planned":
            add("English proficiency", "action", f"IELTS planned; target at least {ie}")
        else:
            add("English proficiency", "action", f"No test score yet; ~{ie} IELTS is typical")

    if opp.get("need_based"):
        if p.get("funding_need") in ("full", "partial"):
            add("Financial need", "met", "Programme is for candidates who need funding")
        else:
            add("Financial need", "unmet", "Programme targets applicants who cannot self-fund")

    return m


def summarise(matrix: list) -> dict:
    t = len(matrix)
    met = sum(1 for x in matrix if x["status"] == "met")
    return {"met": met, "total": t,
            "unmet": sum(1 for x in matrix if x["status"] == "unmet"),
            "actions": sum(1 for x in matrix if x["status"] == "action")}
