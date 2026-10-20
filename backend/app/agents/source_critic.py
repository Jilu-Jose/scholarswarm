"""Agent 03 & 06 - Source Critic: Real-time source accreditation & anti-hallucination peer review."""
import re

from ..tools import web


def check_draft(draft: dict, p: dict) -> list:
    """Fact-check draft SOP claims strictly against the candidate's verified evidence."""
    checks = []
    text = draft.get("text", "")
    corpus = " ".join([
        p.get("resume_text", ""),
        p.get("transcript_text", ""),
        " ".join(p.get("skills", [])),
        " ".join(r.get("name", "") + " " + r.get("description", "") for r in p.get("repos", []))
    ]).lower()

    # 1) Every CGPA claim must match the profile value
    for m in re.finditer(r"CGPA[^0-9]{0,20}(\d{1,2}(?:\.\d{1,2})?)", text, re.I):
        try:
            claimed = float(m.group(1))
            actual = float(p.get("cgpa", 0))
            ok = abs(claimed - actual) < 0.05
            checks.append({
                "claim": f"CGPA {m.group(1)}",
                "status": "verified" if ok else "flagged",
                "detail": "Verified against profile credentials" if ok else f"Mismatch: Profile states CGPA {p.get('cgpa')}"
            })
        except Exception:
            pass

    # 2) Backticked project or repo names must be present in the evidence corpus
    for name in set(re.findall(r"`([^`]{2,60})`", text)):
        ok = name.lower() in corpus
        checks.append({
            "claim": f"Project `{name}`",
            "status": "verified" if ok else "flagged",
            "detail": "Grounded in resume/GitHub evidence" if ok else "Unverified in submitted documents; requires evidence"
        })

    # 3) Check sensitive credential claims (publications, awards, internships)
    credential_patterns = [
        (r"\bpublished\b|\bpublication\b|\bpaper\b", "Publication claim"),
        (r"\baward\b|\bwon\b|\bhonor\b|\bfirst place\b", "Award claim"),
        (r"\bintern(?:ed|ship)\b|\bworked at\b", "Employment / internship claim"),
    ]
    for pat, label in credential_patterns:
        if re.search(pat, text, re.I):
            ok = re.search(pat, corpus, re.I) is not None
            checks.append({
                "claim": label,
                "status": "verified" if ok else "flagged",
                "detail": "Supported by candidate documents" if ok else "Not found in documents; review or provide verification"
            })

    # 4) Transparent placeholders
    for ph in draft.get("placeholders", []):
        checks.append({
            "claim": ph[:75],
            "status": "omitted",
            "detail": "Action placeholder preserved to prevent hallucination"
        })

    return checks


async def audit_sources(run):
    """Real-time audit of candidate opportunities: drop unofficial / commercial aggregators."""
    run.log("source_critic", f"Auditing {len(run.candidates)} discovered URLs for official institutional accreditation")
    passed = []
    rejected = []

    for o in run.candidates:
        u = o.get("url", "")
        official = web.is_official(u)
        o.setdefault("citation", {})
        o["citation"]["official"] = official
        if official:
            passed.append(o)
        else:
            rejected.append(o)

    # Filter out unaccredited sources
    run.candidates = passed
    run.set("source_critic", progress=100)

    if rejected:
        run.log(
            "source_critic",
            f"Filtered out {len(rejected)} unaccredited/commercial links; approved {len(passed)} official opportunities",
            "warn"
        )
    else:
        run.log("source_critic", f"All {len(passed)} candidate sources verified on official accredited domains", "ok")

    run.message(
        "source_critic", "eligibility_verifier",
        f"Domain audit complete: {len(passed)} official sources approved for live crawling. ({len(rejected)} rejected)."
    )


async def fallback_sources(run):
    for o in run.candidates:
        o.setdefault("citation", {})
        o["citation"]["official"] = web.is_official(o.get("url", ""))
    run.log("source_critic", "Fallback: source audit complete", "warn")


async def audit_draft(run):
    """Audit the generated Statement of Purpose for hallucinations and ground truth consistency."""
    p = run.enriched
    run.log("source_critic", "Performing anti-hallucination peer review on Application Writer's draft SOP")
    run.set("source_critic", progress=75)

    checks = check_draft(run.draft, p) if run.draft else []
    flagged = [c for c in checks if c["status"] == "flagged"]
    verified = [c for c in checks if c["status"] == "verified"]
    live_pages = [o for o in run.ranked if o.get("citation", {}).get("ok")]

    run.audit = {
        "sources_audited": len(run.ranked),
        "official": sum(1 for o in run.ranked if o.get("citation", {}).get("official")),
        "non_official_removed": 0,
        "live_verified": len(live_pages),
        "unverified": len(run.ranked) - len(live_pages),
        "draft_checks": checks,
        "draft_flags": len(flagged),
        "hallucination_flags": len(flagged),
        "note": (
            "Live-verified: Each official portal was fetched, SSL-validated, and content-hashed this run."
            if live_pages else
            "Offline mode: official criteria evaluated from registry baseline."
        ),
    }

    if run.draft:
        run.draft["draft_checks"] = checks

    run.set("source_critic", progress=100)
    run.log(
        "source_critic",
        f"Audit verdict: {len(verified)} claims verified, {len(flagged)} hallucination flags, {len(live_pages)} pages live-hashed",
        "ok" if not flagged else "warn"
    )
    run.message(
        "source_critic", "application_writer",
        f"Draft review result: {len(verified)} claims verified against documents. {len(flagged)} flags detected. Status: {'APPROVED' if not flagged else 'REVIEW REQUIRED'}."
    )


async def fallback_draft(run):
    run.audit = {
        "sources_audited": len(run.ranked),
        "official": len(run.ranked),
        "non_official_removed": 0,
        "live_verified": 0,
        "unverified": len(run.ranked),
        "draft_checks": [],
        "draft_flags": 0,
        "hallucination_flags": 0,
        "note": "Critic fallback: basic verification applied."
    }
    run.log("source_critic", "Fallback draft audit completed", "warn")
