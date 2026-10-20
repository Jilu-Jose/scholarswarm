import io
import re

SKILL_VOCAB = [
    "Python", "Java", "C++", "C", "Go", "Rust", "JavaScript", "TypeScript", "SQL", "MATLAB", "R",
    "PyTorch", "TensorFlow", "scikit-learn", "Pandas", "NumPy", "Keras", "HuggingFace", "Transformers",
    "LangChain", "LangGraph", "CrewAI", "FastAPI", "Flask", "Django", "React", "Node.js", "Docker",
    "Kubernetes", "Kafka", "Redis", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP", "Linux", "Git",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Reinforcement Learning",
    "Distributed Systems", "Data Science", "RAG", "LLM", "Robotics", "CAD", "SolidWorks", "ANSYS",
    "CFD", "FEA", "Arduino", "Embedded Systems", "IoT", "Raft", "Statistics", "Data Analysis",
    "Manufacturing", "Sustainability", "Bioinformatics", "Signal Processing", "Quantum Computing",
    "Cybersecurity", "Blockchain", "DevOps", "CI/CD", "Next.js", "GraphQL", "Solidity",
]


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        if name.endswith(".docx"):
            import docx

            d = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in d.paragraphs)
    except Exception as e:  # noqa: BLE001
        return f"[could not parse {filename}: {e}]"
    return data.decode("utf-8", errors="ignore")


def detect_cgpa(text: str):
    """Return (value, scale) if a CGPA/GPA pattern is present."""
    m = re.search(r"(?:CGPA|GPA|C\.G\.P\.A)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?)\s*(?:/|out of)?\s*(10|4|5)?(?:\.0+)?", text, re.I)
    if m:
        val = float(m.group(1))
        scale = float(m.group(2)) if m.group(2) else (10.0 if val > 4.5 else 4.0)
        return val, scale
    return None


def extract_skills(text: str) -> list:
    found = []
    low = text.lower()
    for s in SKILL_VOCAB:
        pat = r"(?<![A-Za-z0-9+#])" + re.escape(s.lower()) + r"(?![A-Za-z0-9+#])"
        if re.search(pat, low):
            found.append(s)
    return found


def extract_projects(text: str, limit: int = 5) -> list:
    """Bullet/heading lines from a 'Projects' section of a resume."""
    m = re.search(r"^\s*projects?\b.*$", text, re.I | re.M)
    if not m:
        return []
    rest = text[m.end():]
    stop = re.search(r"^\s*(education|experience|skills|certifications?|achievements?|publications?|awards?)\b", rest, re.I | re.M)
    block = rest[: stop.start()] if stop else rest
    items = []
    for line in block.splitlines():
        line = line.strip()
        if re.match(r"^[-•*▪]\s*\S", line):
            items.append(re.sub(r"^[-•*▪]\s*", "", line))
    return items[:limit]


def extract_requirements(text: str, limit: int = 4) -> list:
    """Extract bullet points or sentences that describe eligibility requirements from page text."""
    reqs = []
    # Search for requirement headers or keywords
    m = re.search(r"(?:eligibility|admission requirements|who can apply|criteria|qualifications?)\b[:\s]?", text, re.I)
    if m:
        sub = text[m.start(): m.start() + 2500]
        # Look for bullet points or numbered requirements
        lines = sub.split(". ")
        for line in lines:
            line = line.strip()
            if any(k in line.lower() for k in ["degree", "bachelor", "master", "gpa", "ielts", "toefl", "citizen", "national", "experience"]):
                if 20 < len(line) < 180 and line not in reqs:
                    reqs.append(line)
            if len(reqs) >= limit:
                break
    if not reqs:
        # Fallback keyword extraction
        for sentence in re.split(r"[.\n]", text[:8000]):
            s = sentence.strip()
            if any(k in s.lower() for k in ["must have", "minimum cgpa", "minimum gpa", "eligible to apply", "applicants must hold"]):
                if 20 < len(s) < 160 and s not in reqs:
                    reqs.append(s)
            if len(reqs) >= limit:
                break
    return reqs[:limit]


def extract_funding_type(text: str) -> tuple[str, str]:
    """Return (funding_type: 'full'|'partial'|'unknown', funding_summary)."""
    low = text.lower()
    full_indicators = ["fully funded", "full scholarship", "full tuition waiver", "tuition and living allowance", "monthly stipend", "covers tuition fees, monthly allowance"]
    for ind in full_indicators:
        if ind in low:
            # Grab snippet around indicator
            pos = low.find(ind)
            snip = text[max(0, pos - 40): min(len(text), pos + 120)].strip()
            return "full", re.sub(r"\s+", " ", snip)
    if any(k in low for k in ["partial scholarship", "tuition fee waiver", "one-time grant", "financial contribution"]):
        return "partial", "Provides partial funding / tuition waiver. Confirm exact coverage on the official page."
    return "unknown", "Funding details provided on the official portal."


def extract_degree_levels(text: str) -> list:
    """Identify if page specifies Master's, PhD, Bachelor's."""
    low = text.lower()
    levels = []
    if any(k in low for k in ["master's", "masters", "postgraduate", "msc", "m.sc", "m.tech"]):
        levels.append("masters")
    if any(k in low for k in ["phd", "ph.d", "doctoral", "doctorate"]):
        levels.append("phd")
    return levels if levels else ["masters"]


def extract_ielts_requirement(text: str) -> float | None:
    m = re.search(r"ielts\s*(?:overall|band|score)?\s*(?:of|minimum)?\s*(\d(?:\.\d)?)", text, re.I)
    if m:
        try:
            val = float(m.group(1))
            if 4.0 <= val <= 9.0:
                return val
        except Exception:
            pass
    return None


def extract_work_years_requirement(text: str) -> int:
    m = re.search(r"(\d+)\s*years?\s*(?:of\s*)?(?:work\s*|professional\s*)?experience", text, re.I)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    return 0
