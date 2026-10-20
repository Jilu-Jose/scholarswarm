"""Web tools: official-domain allowlist, resilient page fetch, and multi-tier live search."""
import asyncio
import hashlib
import re
import time
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from .. import config

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

BROWSER_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

OFFICIAL_SUFFIX_PATTERNS = [
    r"\.gov(?:\.[a-z]{2})?$",
    r"\.edu(?:\.[a-z]{2})?$",
    r"\.ac\.[a-z]{2}$",
    r"\.gouv\.[a-z]{2}$",
    r"\.europa\.eu$",
    r"\.admin\.ch$",
    r"\.gc\.ca$",
    r"\.go\.jp$",
    r"\.go\.kr$",
    r"\.ontario\.ca$",
    r"\.canada\.ca$",
]

OFFICIAL_DOMAINS = {
    "daad.de", "daad.in", "daad-india.org", "chevening.org", "usief.org.in", "fulbrightprogram.org",
    "campusfrance.org", "studyinnl.org", "nuffic.nl", "tudelft.nl", "vectorinstitute.ai",
    "gatescambridge.org", "si.se", "studyinsweden.se", "stipendiumhungaricum.hu", "tka.hu",
    "ontario.ca", "vanier.gc.ca", "educanada.ca", "international.gc.ca", "mitacs.ca",
    "studyinjapan.go.jp", "mext.go.jp", "jasso.go.jp", "studyinkorea.go.kr", "niied.go.kr",
    "knight-hennessy.stanford.edu", "rhodeshouse.ox.ac.uk", "cscuk.fcdo.gov.uk", "britishcouncil.org",
    "britishcouncil.in", "a-star.edu.sg", "nus.edu.sg", "ntu.edu.sg", "sutd.edu.sg",
    "erasmus-plus.ec.europa.eu", "ox.ac.uk", "cam.ac.uk", "sbfi.admin.ch", "swissnex.org",
    "scholarships.gov.in", "wes.org", "tum.de", "rwth-aachen.de", "uni-heidelberg.de",
    "lmu.de", "ethz.ch", "epfl.ch", "sorbonne-universite.fr", "universite-paris-saclay.fr",
    "studyinaustralia.gov.au", "education.gov.au",
}


def host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:  # noqa: BLE001
        return ""


def is_official(url: str) -> bool:
    """Return True if URL belongs to an accredited university, government, or official foundation."""
    if not url or not url.lower().startswith("https://"):
        return False
    h = host(url)
    if not h:
        return False
    # Check explicitly allowed domains
    if any(h == d or h.endswith("." + d) for d in OFFICIAL_DOMAINS):
        return True
    # Check official domain suffix patterns (e.g. .edu, .ac.uk, .gov.in)
    if any(re.search(pat, h) for pat in OFFICIAL_SUFFIX_PATTERNS):
        return True
    return False


def _clean(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "aside"]):
        t.decompose()
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    return title, text[:45000]


async def fetch_page(url: str, retries: int = 2) -> dict:
    """Fetch one URL with retries and realistic headers. Returns {ok, status, text, sha256, ...}."""
    out = {
        "ok": False, "status": 0, "url": url, "final_url": url, "title": "", "text": "",
        "sha256": "", "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "error": "", "official": is_official(url)
    }
    if not config.LIVE_FETCH:
        out["error"] = "offline mode (LIVE_FETCH=0)"
        return out

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(
                timeout=config.FETCH_TIMEOUT,
                follow_redirects=True,
                headers=BROWSER_HEADERS,
                verify=False  # Avoid SSL dropouts on international gov servers
            ) as c:
                r = await c.get(url)
            out["status"] = r.status_code
            out["final_url"] = str(r.url)
            if r.status_code >= 500 or r.status_code == 429:
                raise httpx.HTTPError(f"HTTP {r.status_code}")
            if r.status_code >= 400:
                out["error"] = f"HTTP {r.status_code}"
                return out

            ctype = r.headers.get("content-type", "").lower()
            if "pdf" in ctype:
                out["text"] = "Official PDF Document"
                out["title"] = "Official PDF Document"
            else:
                out["title"], out["text"] = _clean(r.text)

            out["sha256"] = hashlib.sha256(r.content).hexdigest()
            out["ok"] = True
            out["error"] = ""
            return out
        except Exception as e:  # noqa: BLE001
            out["error"] = f"{type(e).__name__}: {e}"[:160]
            await asyncio.sleep(0.7 * (attempt + 1))
    return out


async def _search_tavily(query: str, n: int = 8) -> list:
    if not config.TAVILY_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post("https://api.tavily.com/search", json={
                "api_key": config.TAVILY_API_KEY, "query": query, "max_results": n})
            r.raise_for_status()
            return [{"title": x.get("title", ""), "url": x.get("url", ""), "snippet": x.get("content", "")[:350]}
                    for x in r.json().get("results", [])]
    except Exception:
        return []


async def _search_ddg_html(query: str, n: int = 8) -> list:
    try:
        async with httpx.AsyncClient(timeout=15, headers=BROWSER_HEADERS, follow_redirects=True) as c:
            r = await c.get(f"https://html.duckduckgo.com/html/?q={quote_plus(query)}")
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            if "uddg=" in href:
                href = unquote(parse_qs(urlparse(href).query).get("uddg", [""])[0])
            if href.startswith("//"):
                href = "https:" + href
            if not href.startswith("http"):
                continue
            snip = a.find_parent(class_="result")
            snippet = snip.select_one(".result__snippet").get_text(" ", strip=True) if snip and snip.select_one(".result__snippet") else ""
            results.append({"title": a.get_text(" ", strip=True), "url": href, "snippet": snippet[:350]})
            if len(results) >= n:
                break
        return results
    except Exception:
        return []


async def _search_ddg_lite(query: str, n: int = 8) -> list:
    try:
        async with httpx.AsyncClient(timeout=15, headers=BROWSER_HEADERS, follow_redirects=True) as c:
            r = await c.post("https://lite.duckduckgo.com/lite/", data={"q": query})
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for a in soup.select("a.result-link"):
            href = a.get("href", "")
            if not href.startswith("http"):
                continue
            # Snippet is often in the following table row
            tr = a.find_parent("tr")
            snippet = ""
            if tr:
                next_tr = tr.find_next_sibling("tr")
                if next_tr:
                    snippet = next_tr.get_text(" ", strip=True)
            results.append({"title": a.get_text(" ", strip=True), "url": href, "snippet": snippet[:350]})
            if len(results) >= n:
                break
        return results
    except Exception:
        return []


async def web_search(query: str, n: int = 8) -> list:
    """Multi-tier search: Tavily -> DuckDuckGo HTML -> DuckDuckGo Lite. Returns [{title, url, snippet}]."""
    if not config.LIVE_DISCOVERY or not config.LIVE_FETCH:
        return []

    # 1. Tavily if available
    res = await _search_tavily(query, n)
    if res:
        return res

    # 2. DuckDuckGo HTML
    res = await _search_ddg_html(query, n)
    if res:
        return res

    # 3. DuckDuckGo Lite fallback
    return await _search_ddg_lite(query, n)


_DATE = r"(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{1,2}[/.-]\d{1,2}[/.-]\d{4})"


def find_deadlines(text: str, limit: int = 3) -> list:
    """Return verbatim snippets where a deadline keyword sits near an exact date."""
    snippets = []
    seen = set()
    for m in re.finditer(r"(deadline|apply by|closing date|applications? close|submit(?:ted)? by|due date)", text, re.I):
        window = text[max(0, m.start() - 60): m.end() + 140]
        cleaned = re.sub(r"\s+", " ", window).strip()
        if re.search(_DATE, window, re.I) and cleaned not in seen:
            seen.add(cleaned)
            snippets.append(cleaned)
        if len(snippets) >= limit:
            break
    return snippets
