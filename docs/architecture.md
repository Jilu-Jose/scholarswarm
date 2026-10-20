# ScholarSwarm architecture

```mermaid
flowchart LR
  UI[Frontend<br/>profile · live swarm · matches · draft] -->|POST /api/swarm/start| ORCH
  ORCH -->|SSE /stream| UI
  subgraph ORCH[Orchestrator: shared blackboard + retry/fallback runner]
    A1[01 Profile Analyst] --> A2[02 Opportunity Scout] --> A3[03 Eligibility Verifier] --> A4[04 Match Ranker] --> A5[05 Application Writer] --> A6[06 Source Critic]
  end
  A1 -.-> GH[(GitHub API)]
  A1 -.-> EX[(user-supplied URLs)]
  A2 -.-> REG[(curated official registry)]
  A2 -.-> WS[(Tavily / DuckDuckGo)]
  A3 -.-> OFF[(official pages + archive mirror)]
  A3 --> RULES[Deterministic rules engine]
  A1 & A4 & A5 -.-> LLM[(OpenAI-compatible LLM, optional)]
  A6 -->|drops non-official, flags unsupported claims| ORCH
```

## Message flow (blackboard)

| Agent | Reads | Writes |
|---|---|---|
| 01 Profile Analyst | form, resume, transcript, GitHub, extra URLs | `enriched` profile, strengths, score |
| 02 Opportunity Scout | `enriched` | `candidates` (registry + live web, official domains only) |
| 03 Eligibility Verifier | `candidates`, `enriched` | citations (status, hash, time), deadline evidence, eligibility matrix |
| 04 Match Ranker | matrices | scores, `top5`, fit notes |
| 05 Application Writer | top pick, `enriched` | SOP draft with `[ACTION REQUIRED]` placeholders |
| 06 Source Critic | everything | audit, removes non-official picks, flags unsupported draft claims |

## Failure recovery

- Every agent runs under `step()`: retry, then a deterministic fallback.
- Page fetch: retry with backoff, then official fallback URLs, then an archive snapshot (labelled), else "unverified".
- LLM missing or failing: every agent has a rules/template path, so the swarm always completes.
- GitHub down: continue with resume evidence only.

## Adapting to a new profile (the live surprise)

Nothing is hard-coded to Rahul. Scoring, discovery queries and the SOP are all driven by the submitted profile
(degree level, field, destinations, funding need, IELTS, work experience). Load the `Ananya` sample, or type any profile, and press Deploy.
