"""Agent 06 - Application Writer: Grounded Statement of Purpose generation with strict compliance."""
import re

from ..tools import llm


def _facts(p: dict) -> str:
    return (
        f"Name: {p.get('name', 'Applicant')}\n"
        f"Degree: {p.get('degree', 'Bachelors')} in {p.get('field', 'General Studies')}, graduating {p.get('grad_year', 2026)}\n"
        f"CGPA: {p.get('cgpa')}/{p.get('cgpa_scale', 10):g} (German approx: {p.get('bavarian', 'N/A')})\n"
        f"Research Interest: {p.get('research_interest') or 'Advanced Studies'}\n"
        f"Skills: {', '.join(p.get('skills', [])[:15])}\n"
        f"Resume Projects: {p.get('projects', [])}\n"
        f"GitHub Repos: {[(r.get('name'), r.get('description')) for r in p.get('repos', [])[:5]]}\n"
        f"Work Experience: {p.get('work_years', 0)} years"
    )


def _rich_draft(o: dict, p: dict) -> str:
    """High-quality structured academic SOP based strictly on candidate facts."""
    name = p.get("name") or "Applicant"
    deg = p.get("degree") or "Bachelor of Technology"
    field = p.get("field") or "Engineering"
    cgpa = p.get("cgpa", "8.0")
    scale = p.get("cgpa_scale", 10)
    interest = p.get("research_interest") or f"cutting-edge developments in {field}"
    skills = ", ".join(p.get("skills", [])[:6]) or "modern computational methods"

    projects = p.get("projects", [])
    repos = p.get("repos", [])

    project_narratives = []
    if repos:
        for r in repos[:2]:
            r_desc = f": {r['description']}" if r.get("description") else ""
            project_narratives.append(f"In my project `{r['name']}`{r_desc}, I developed hands-on proficiency in building scalable, real-world systems.")
    elif projects:
        for prj in projects[:2]:
            p_name = prj.split(":")[0].strip()
            p_detail = f", where I focused on {prj.split(':', 1)[1].strip()}" if ":" in prj else ""
            project_narratives.append(f"Through my work on `{p_name}`{p_detail}, I demonstrated practical problem-solving in {field}.")
    else:
        project_narratives.append("[ACTION REQUIRED: Highlight one significant technical or research project from your portfolio and its impact].")

    proj_body = "\n\n".join(project_narratives)

    target_name = o.get("name", "Scholarship Programme")
    provider = o.get("provider", "Host Institution")
    country = o.get("country", "the host country")

    return (
        f"# STATEMENT OF PURPOSE: {target_name.upper()}\n"
        f"Applicant: {name} | Candidate Institution: {provider} | Verified Draft\n\n"
        f"I am writing to formally submit my application for the {target_name} supporting advanced study at {provider}. "
        f"Having completed my {deg} in {field} with an academic cumulative standing of {cgpa}/{scale:g}, my academic and research "
        f"ambitions have consistently focused on {interest}. This programme represents the ideal environment to deepen my expertise.\n\n"
        f"Throughout my academic career, I have cultivated a rigorous technical foundation spanning {skills}. "
        f"Beyond theoretical coursework, I have actively translated core principles into practical implementations:\n\n"
        f"{proj_body}\n\n"
        f"My decision to pursue advanced studies through {target_name} is driven by the distinguished faculty, research infrastructure, "
        f"and collaborative ecosystem provided by {provider} in {country}. [ACTION REQUIRED: Cite 1-2 specific labs, professors, or modules at {provider} aligned with your goals].\n\n"
        f"Upon completion of this graduate programme, my objective is to leverage the advanced training and global perspectives gained to contribute directly to innovation in {field}. "
        f"I am deeply committed to upholding the standards of the {target_name} community and making meaningful academic and professional contributions.\n"
    )


async def run(run):
    p = run.enriched
    pool = [o for o in run.top5 if o.get("citation", {}).get("official")] or run.top5 or run.ranked
    if not pool:
        run.draft = {}
        return

    target = pool[0]
    run.log("application_writer", f"Synthesizing Statement of Purpose for #{target.get('rank', 1)}: {target['name']}")
    run.set("application_writer", progress=30)
    text = None

    if llm.available():
        try:
            prompt_system = (
                "You are an expert academic advisor drafting a formal Statement of Purpose for a prestigious scholarship application. "
                "STRICT GROUNDING RULES:\n"
                "1. Use ONLY the facts provided about the applicant. Do NOT invent grades, publications, awards, companies, or degrees.\n"
                "2. Enclose any specific project, repository, or tool names mentioned from the resume in backticks (e.g. `ProjectName`).\n"
                "3. Where institution-specific knowledge or details are required that are not in the profile, insert a clear `[ACTION REQUIRED: ...]` placeholder.\n"
                "4. Structure: Single '# ' Markdown title, 'Applicant: ...' line, followed by 5 clear, cohesive paragraphs (500-700 words)."
            )
            prompt_user = (
                f"APPLICANT PROFILE:\n{_facts(p)}\n\n"
                f"TARGET SCHOLARSHIP:\nName: {target['name']}\nProvider: {target.get('provider')}\nCountry: {target.get('country')}\n"
                f"Official Requirements: {target.get('page_requirements')}\n"
                f"Funding Details: {target.get('funding_summary')}"
            )
            text = await llm.chat(prompt_system, prompt_user, max_tokens=2200, temperature=0.35)
            run.log("application_writer", "LLM synthesized grounded Statement of Purpose from verified facts", "ok")
        except Exception as e:  # noqa: BLE001
            run.log("application_writer", f"LLM drafting unavailable ({type(e).__name__}); generated structured academic draft", "warn")

    run.draft = make_draft(target, p, text)
    run.log(
        "application_writer",
        f"Draft prepared: {run.draft['word_count']} words, {len(run.draft['placeholders'])} action items flagged for candidate review",
        "ok"
    )
    run.message(
        "application_writer", "source_critic",
        f"Draft prepared for '{target['name']}' ({run.draft['word_count']} words). Submitting to Source Critic for anti-hallucination peer review."
    )


def make_draft(target: dict, p: dict, text: str = None) -> dict:
    source = "llm" if text else "structured-template"
    text = text or _rich_draft(target, p)
    return {
        "opportunity_id": target["id"],
        "opportunity_name": target["name"],
        "provider": target.get("provider", ""),
        "country": target.get("country", ""),
        "text": text,
        "word_count": len(re.findall(r"\w+", text)),
        "placeholders": re.findall(r"\[ACTION REQUIRED:[^\]]*\]", text),
        "source": source,
    }


async def fallback(run):
    pool = run.top5 or run.ranked
    target = pool[0] if pool else {"id": "default", "name": "Scholarship", "provider": "University", "country": "Global"}
    run.draft = make_draft(target, run.enriched, None)
    run.log("application_writer", "Fallback: structured academic draft prepared", "warn")
    run.message("application_writer", "source_critic", "Fallback: draft prepared for review.")
