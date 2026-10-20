"""Swarm orchestrator: dynamic inter-agent blackboard, real-time message bus, and resilient execution."""
import asyncio
import json
import time
import traceback
import uuid

from . import config
from .models import Profile

AGENTS = [
    ("profile_analyst", "Profile Analyst", "01", "Analyzes resume, transcript, GitHub and academic credentials"),
    ("opportunity_scout", "Opportunity Scout", "02", "Conducts multi-vector live web searches and registry exploration"),
    ("source_critic", "Source Critic", "03", "Audits domains in real time, drops non-official links, and fact-checks drafts"),
    ("eligibility_verifier", "Eligibility Verifier", "04", "Probes official portals, hashes content, and evaluates criteria"),
    ("match_ranker", "Match Ranker", "05", "Scores multidimensional academic, destination, and funding fit"),
    ("application_writer", "Application Writer", "06", "Synthesizes grounded Statements of Purpose with peer review"),
]
NAMES = {a[0]: a[1] for a in AGENTS}

RUNS: dict = {}


class Run:
    def __init__(self, profile: Profile):
        self.id = uuid.uuid4().hex[:8]
        self.profile = profile
        self.t0 = time.time()
        self.events: list = []
        self.messages: list = []
        self.finished = False
        self.error = None
        self.agents = {a[0]: {"id": a[0], "name": a[1], "num": a[2], "role": a[3],
                              "status": "idle", "progress": 0, "detail": ""} for a in AGENTS}
        # Shared Swarm Blackboard
        self.enriched: dict = {}
        self.briefing: dict = {}
        self.candidates: list = []
        self.verified_pool: list = []
        self.ranked: list = []
        self.top5: list = []
        self.audit: dict = {}
        self.draft: dict = {}
        self.stats = {"retries": 0, "fallbacks": 0, "messages_exchanged": 0}
        self.result: dict = {}

    def ts(self) -> str:
        s = int(time.time() - self.t0)
        return f"00:{s // 60:02d}:{s % 60:02d}"

    def log(self, agent: str, msg: str, level: str = "info"):
        self.events.append({
            "type": "log", "t": self.ts(), "agent": agent, "name": NAMES.get(agent, agent),
            "msg": msg, "level": level
        })

    def message(self, from_agent: str, to_agent: str, msg: str, level: str = "info"):
        """Inter-agent communication over the Swarm Message Bus."""
        self.stats["messages_exchanged"] += 1
        item = {
            "type": "message",
            "t": self.ts(),
            "from": from_agent,
            "from_name": NAMES.get(from_agent, from_agent),
            "to": to_agent,
            "to_name": NAMES.get(to_agent, to_agent),
            "msg": msg,
            "level": level,
        }
        self.messages.append(item)
        self.events.append(item)

    def set(self, agent: str, status: str = None, progress: int = None, detail: str = None):
        a = self.agents[agent]
        if status:
            a["status"] = status
        if progress is not None:
            a["progress"] = max(0, min(100, int(progress)))
        if detail is not None:
            a["detail"] = detail
        self.events.append({"type": "agent", **a})


async def step(run: Run, agent: str, fn, fallback=None, attempts: int = 2):
    """Run an agent with failure recovery and deterministic fallbacks."""
    run.set(agent, "working", 0)
    for i in range(attempts):
        try:
            await fn(run)
            run.set(agent, "done", 100)
            return True
        except Exception as e:  # noqa: BLE001
            last = i == attempts - 1
            run.stats["retries"] += 0 if last else 1
            run.log(agent, f"{type(e).__name__}: {str(e)[:140]}. {'Switching to fallback strategy' if last else 'Retrying'}...", "warn")
            run.set(agent, "retrying", None, "recovering from fault")
            await asyncio.sleep(0.8)
    if fallback:
        try:
            run.stats["fallbacks"] += 1
            await fallback(run)
            run.set(agent, "done", 100, "completed via fallback")
            return True
        except Exception as e:  # noqa: BLE001
            run.log(agent, f"Fallback failed: {e!r}", "error")
            run.log(agent, traceback.format_exc()[-300:], "error")
    run.set(agent, "failed", None, "failed")
    return False


async def execute(run: Run):
    """Execute the swarm with dynamic inter-agent coordination."""
    from .agents import (application_writer, eligibility_verifier, match_ranker,
                         opportunity_scout, profile_analyst, source_critic)
    try:
        # Phase 1: Profile Digest & Briefing
        await step(run, "profile_analyst", profile_analyst.run, profile_analyst.fallback)

        # Phase 2: Live Discovery & Real-Time Source Auditing
        await step(run, "opportunity_scout", opportunity_scout.run, opportunity_scout.fallback)
        await step(run, "source_critic", source_critic.audit_sources, source_critic.fallback_sources)

        # Phase 3: Parallel Verification & Evidence Extraction
        await step(run, "eligibility_verifier", eligibility_verifier.run, eligibility_verifier.fallback)

        # Phase 4: Multidimensional Match Ranking
        await step(run, "match_ranker", match_ranker.run, match_ranker.fallback)

        # Phase 5: Grounded SOP Drafting & Peer-Review Fact Check
        await step(run, "application_writer", application_writer.run, application_writer.fallback)
        await step(run, "source_critic", source_critic.audit_draft, source_critic.fallback_draft)

        build_result(run)
        run.events.append({"type": "result"})
    except Exception as e:  # noqa: BLE001
        run.error = str(e)
        run.log("profile_analyst", f"Swarm interrupted: {e!r}", "error")
        run.events.append({"type": "error", "msg": str(e)})
    finally:
        run.finished = True
        try:
            (config.RUNS_DIR / f"{run.id}.json").write_text(json.dumps(run.result, indent=2, default=str))
        except Exception:  # noqa: BLE001
            pass


def build_result(run: Run):
    run.result = {
        "run_id": run.id,
        "elapsed_s": int(time.time() - run.t0),
        "profile": run.enriched,
        "candidates": run.ranked,
        "top5": run.top5,
        "draft": run.draft,
        "audit": run.audit,
        "messages": run.messages,
        "stats": {
            **run.stats,
            "candidates": len(run.ranked),
            "verified": sum(1 for o in run.ranked if o.get("citation", {}).get("ok")),
            "llm": bool(config.LLM_API_KEY),
            "live": config.LIVE_FETCH,
        },
    }
