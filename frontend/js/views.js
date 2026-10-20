const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const DESTS = ["Germany", "Canada", "Singapore", "United Kingdom", "United States", "Netherlands", "Japan", "Sweden", "France", "Switzerland", "South Korea", "Hungary", "Australia"];

const ICONS = {
  check: '<svg class="icon" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>',
  x: '<svg class="icon" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  alert: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
  help: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  shieldCheck: '<svg class="icon" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>',
  clock: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  messages: '<svg class="icon" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
  terminal: '<svg class="icon" viewBox="0 0 24 24"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
  star: '<svg class="icon" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
  refresh: '<svg class="icon" viewBox="0 0 24 24"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>',
  copy: '<svg class="icon" viewBox="0 0 24 24"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>',
  filePdf: '<svg class="icon" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M10 12h1a1 1 0 0 1 1 1v1a1 1 0 0 1-1 1h-1v-3z"/></svg>',
  fileDocx: '<svg class="icon" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 13v4m6-4v4m-3-2v2"/></svg>',
  pen: '<svg class="icon" viewBox="0 0 24 24"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>',
  user: '<svg class="icon" viewBox="0 0 24 24"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  arrowRight: '<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>'
};

function ic(name, extraClass) {
  const svg = ICONS[name] || "";
  if (!extraClass) return svg;
  return svg.replace('class="icon"', `class="icon ${extraClass}"`);
}

const ICON = {
  met: ic("check", "icon-sm icon-met"),
  unmet: ic("x", "icon-sm icon-unmet"),
  action: ic("alert", "icon-sm icon-action"),
  unknown: ic("help", "icon-sm icon-unknown")
};

function vOverview(S) {
  const r = S.result;
  const isLlm = S.health && S.health.llm;
  return `<div class="head"><div><span class="pill green"><span class="dot"></span> SWARM CONSOLE</span><h1 class="page-t">Welcome${S.profile.name ? ", " + esc(S.profile.name.split(" ")[0]) : ""}</h1>
  <p class="muted">ScholarSwarm orchestrates six specialized AI agents to discover official scholarships, verify eligibility live, and draft grounded applications.</p></div>
  <a class="btn primary" href="#profile">${S.runId ? "Edit profile" : "Set up your Profile"} ${ic("arrowRight")}</a></div>
  <div class="grid g3">
    <div class="card"><div class="label">Run status</div><div class="stat">${S.runId ? (S.finished ? "Completed" : "Running…") : "Idle"}</div><p class="muted" style="font-size:13px">${S.runId ? "Cluster Run #" + S.runId : "Configure profile and deploy swarm"}</p></div>
    <div class="card"><div class="label">Candidates Discovered</div><div class="stat">${r ? r.stats.candidates : "–"}</div><p class="muted" style="font-size:13px">${r ? r.stats.verified + " official portals verified live" : "Deploy agents to initiate live crawl"}</p></div>
    <div class="card"><div class="label">Agent Intelligence</div><div class="stat" style="font-size:26px">${isLlm ? "Cloud LLM Active" : "NLP + Rules Engine"}</div><p class="muted" style="font-size:13px">${isLlm ? esc(S.health.model) : "Configure LLM_API_KEY in backend/.env for AI synthesis"}</p></div>
  </div>
  <div class="card" style="margin-top:20px">
    <div class="label">Autonomous Swarm Architecture</div>
    <div class="grid g6" style="margin-top:14px">
      <div class="cluster-chip"><span class="mono muted">#01 PROFILE</span><b>Profile Analyst</b>Credential extraction &amp; scoring</div>
      <div class="cluster-chip"><span class="mono muted">#02 SCOUT</span><b>Opportunity Scout</b>Multi-vector live web discovery</div>
      <div class="cluster-chip"><span class="mono muted">#03 AUDITOR</span><b>Source Critic</b>Real-time accreditation &amp; audit</div>
      <div class="cluster-chip"><span class="mono muted">#04 VERIFIER</span><b>Eligibility Verifier</b>Parallel crawl &amp; rules evaluation</div>
      <div class="cluster-chip"><span class="mono muted">#05 RANKER</span><b>Match Ranker</b>Multidimensional algorithmic fit</div>
      <div class="cluster-chip"><span class="mono muted">#06 WRITER</span><b>Application Writer</b>Grounded SOP with peer review</div>
    </div>
  </div>`;
}

function chips(list, on, attr) {
  return list.map((d) => `<button type="button" class="chip ${on.includes(d) ? "on" : ""}" data-${attr}="${esc(d)}">${on.includes(d) ? ic("check", "icon-sm") + " " : "+ "}${esc(d)}</button>`).join("");
}

function vProfile(S) {
  const p = S.profile;
  const up = (kind, label, req) => {
    const u = S.uploads[kind];
    return `<div class="card" style="margin-bottom:14px"><div class="label">${label} · ${req}</div>
      <div class="drop" style="margin-top:10px">${u ? `<b>${esc(u.filename)}</b><div class="muted">${(u.size / 1024).toFixed(0)} KB · ${u.chars} chars read</div>
        <div style="margin-top:8px;font-size:12px">Extracted: ${esc((u.skills || []).slice(0, 8).join(", ") || "no skills detected")}${u.cgpa ? " · CGPA " + u.cgpa : ""}</div>`
        : `<div class="muted">Upload PDF, DOCX or TXT</div>`}
        <input type="file" id="up_${kind}" accept=".pdf,.docx,.txt,.md" style="margin-top:8px;font-size:12px"></div></div>`;
  };
  return `<div class="head"><div><span class="pill green">STEP 01 OF 04 · PROFILE DIGESTION</span>
    <h1 class="page-t">Student Profile &amp; Academic Credentials</h1>
    <p class="muted">Provide your genuine academic background. Uploading your CV auto-populates skills, projects, and GPA.</p></div>
    <div class="card" style="padding:12px 18px"><div class="label">Automated Profile Extraction</div>
      <div class="muted" style="font-size:12.5px;margin-top:4px">Upload your Resume or Academic Transcripts for automatic extraction.</div></div></div>
  <div class="layout2"><div>
    ${up("resume", "Curriculum Vitae / Resume", "Required")}${up("transcript", "Academic Transcripts", "Optional")}
    <div class="card"><div class="label">Privacy &amp; Data Security</div><p class="muted" style="font-size:13px;margin:8px 0 0">All documents are parsed in memory for this session only. Raw files are never stored or shared with external parties.</p></div>
  </div>
  <div class="card">
    <h3 style="font-size:22px;margin-bottom:14px">1. Academic &amp; Personal Foundation</h3>
    <div class="two"><div class="field"><span class="label">Full Name</span><input id="f_name" placeholder="e.g. Maya Patel" value="${esc(p.name)}"></div>
      <div class="field"><span class="label">Degree &amp; Specialization</span><input id="f_field" placeholder="e.g. B.Tech Computer Science" value="${esc(p.field)}"></div></div>
    <div class="two"><div class="field"><span class="label">Current CGPA / GPA</span><input id="f_cgpa" type="number" step="0.01" placeholder="8.5" value="${p.cgpa || ''}"></div>
      <div class="field"><span class="label">Scale</span><select id="f_scale"><option ${p.cgpa_scale == 10 ? "selected" : ""}>10</option><option ${p.cgpa_scale == 4 ? "selected" : ""}>4</option></select></div></div>
    <div class="two"><div class="field"><span class="label">Graduation Year</span><input id="f_year" type="number" value="${p.grad_year}"></div>
      <div class="field"><span class="label">Work Experience (Years)</span><input id="f_work" type="number" step="0.5" value="${p.work_years}"></div></div>
    <div class="field"><span class="label">Home Country &amp; City</span><input id="f_loc" placeholder="e.g. Bangalore, India" value="${esc(p.location)}"></div>
    <h3 style="font-size:22px;margin:18px 0 12px">2. Public Technical Footprint</h3>
    <div class="two"><div class="field"><span class="label">GitHub Handle or URL</span><input id="f_github" placeholder="github.com/your-username" value="${esc(p.github)}"></div>
      <div class="field"><span class="label">LinkedIn / Portfolio URL</span><input id="f_linkedin" placeholder="https://linkedin.com/in/..." value="${esc(p.linkedin)}"></div></div>
    <div class="field"><span class="label">Other Public Profile URLs (comma separated)</span><input id="f_extra" placeholder="https://scholar.google.com/..., https://yoursite.dev" value="${esc((p.extra_urls || []).join(", "))}"></div>
    <h3 style="font-size:22px;margin:18px 0 12px">3. Target Destination &amp; Scope</h3>
    <div class="label" style="margin-bottom:8px">Preferred Destinations (tap to toggle)</div>
    <div class="chips" id="destChips">${chips(DESTS, p.destinations, "dest")}</div>
    <div class="two" style="margin-top:16px"><div><div class="label" style="margin-bottom:8px">Target Degree</div>
      <div class="chips" id="degChips"><button type="button" class="chip ${p.target_degree == "masters" ? "on" : ""}" data-deg="masters">Master's</button><button type="button" class="chip ${p.target_degree == "phd" ? "on" : ""}" data-deg="phd">PhD / Research</button></div></div>
      <div class="field"><span class="label">Field of Research / Specialization</span><input id="f_interest" placeholder="e.g. Distributed Systems, Robotics" value="${esc(p.research_interest)}"></div></div>
    <div class="two"><div class="field"><span class="label">Funding Requirement</span><select id="f_funding"><option value="full" ${p.funding_need == "full" ? "selected" : ""}>Need full funding (Tuition + Stipend)</option><option value="partial" ${p.funding_need == "partial" ? "selected" : ""}>Partial funding / tuition waiver is fine</option><option value="none" ${p.funding_need == "none" ? "selected" : ""}>Self-funded</option></select></div>
      <div class="field"><span class="label">English Proficiency (IELTS)</span><div class="two"><select id="f_ielts_status"><option value="none" ${p.ielts_status == "none" ? "selected" : ""}>No test yet</option><option value="planned" ${p.ielts_status == "planned" ? "selected" : ""}>Planned / In progress</option><option value="have" ${p.ielts_status == "have" ? "selected" : ""}>Have score</option></select><input id="f_ielts" type="number" step="0.5" placeholder="Band" value="${p.ielts_score ?? ""}"></div></div></div>
  </div></div>
  <div class="stickybar"><span class="muted" style="font-size:13px">${ic("shieldCheck")} 100% verified official sources · applications are never submitted without your manual approval.</span>
    <div class="row"><button class="btn" id="saveDraft">Save Profile</button><button class="btn primary" id="deploy">Deploy AI Agent Swarm ${ic("arrowRight")}</button></div></div>`;
}

function agentCard(a) {
  const dot = a.status === "working" || a.status === "done" ? "" : a.status === "retrying" ? "amber" : "idle";
  const label = { idle: "Idle", working: "Working", done: "Done", retrying: "Retrying", failed: "Failed" }[a.status] || a.status;
  return `<div class="agent ${a.status}"><div style="display:flex;justify-content:space-between"><span class="dot ${dot}"></span><span class="pill ${a.status === "done" || a.status === "working" ? "green" : a.status === "retrying" ? "amber" : a.status === "failed" ? "red" : ""}">${label}</span></div>
    <div class="mono muted" style="margin-top:6px">AGENT-${a.num}</div><b style="font-size:14px">${esc(a.name)}</b><div class="muted">${esc(a.role)}</div>
    ${a.detail ? `<div class="mono" style="font-size:10px;color:var(--amber)">${esc(a.detail)}</div>` : ""}
    <div class="bar"><i style="width:${a.progress}%"></i></div></div>`;
}

function vSwarm(S) {
  if (!S.runId) return `<div class="empty card"><h2>No active swarm cluster</h2><p>Provide your profile credentials and deploy your agents.</p><a class="btn primary" href="#profile">Go to Profile Setup</a></div>`;
  const agents = S.agents.length ? S.agents : [];
  const pct = agents.length ? Math.round(agents.reduce((s, a) => s + a.progress, 0) / agents.length) : 0;
  const e = S.enriched;

  const logsHTML = S.events.filter((x) => x.type === "log").map((x) =>
    `<div class="l"><span class="t">[${x.t}]</span><span class="a">[${esc(x.name)}]</span> <span class="${x.level}">${esc(x.msg)}</span></div>`
  ).join("");

  const messagesHTML = (S.messages || []).map((m) =>
    `<div class="msg-card">
      <div class="msg-meta">
        <span class="msg-from">${esc(m.from_name)}</span>
        <span style="opacity:.6">${ic("arrowRight")}</span>
        <span class="msg-to">${esc(m.to_name)}</span>
        <span class="msg-time">[${esc(m.t)}]</span>
      </div>
      <div>${esc(m.msg)}</div>
    </div>`
  ).join("");

  return `<div class="card" style="margin-bottom:6px"><div class="head" style="margin:0"><div><h1 class="page-t" style="margin:0">${S.finished ? "Swarm Execution Complete" : "Agent Swarm Collaborating…"}</h1>
    <p class="muted" style="margin:4px 0 0;font-size:13px">Autonomous multi-agent discovery, parallel crawling, and grounded synthesis.</p></div>
    <div class="row"><span class="pill">CLUSTER #${esc(S.runId)}</span><span class="pill">${ic("clock", "icon-sm")} ${S.elapsed || "00:00:00"}</span>
    <a class="btn primary" href="#matches" ${S.finished ? "" : 'style="opacity:.5;pointer-events:none"'}>View Verified Matches ${S.result ? `<span class="pill">${S.result.top5.length} ready</span>` : ""}</a></div></div>
    <div class="progress" style="margin-top:14px"><i style="width:${S.finished ? 100 : pct}%"></i></div><div class="mono muted" style="font-size:11px;margin-top:6px">${S.finished ? 100 : pct}% cluster completion</div></div>
  <div class="agents">${agents.map(agentCard).join("")}</div>

  <div class="tab-row">
    <button type="button" class="tab-btn ${S.swarmTab !== 'logs' ? 'on' : ''}" data-stab="messages">${ic("messages")} Swarm Dialogue Bus (${(S.messages || []).length})</button>
    <button type="button" class="tab-btn ${S.swarmTab === 'logs' ? 'on' : ''}" data-stab="logs">${ic("terminal")} Agent Execution Logs (${S.events.filter((x) => x.type === 'log').length})</button>
  </div>

  <div class="layout3">
    <div>
      ${S.swarmTab === 'logs'
        ? `<div class="term" id="term">${logsHTML || '<span class="muted">Awaiting agent logs…</span>'}</div>`
        : `<div class="msg-feed" id="term">${messagesHTML || '<span class="muted" style="padding:14px">Awaiting agent dialogue on SwarmBus…</span>'}</div>`
      }
    </div>
    <div class="card">${e ? `<div style="display:flex;justify-content:space-between"><div><b style="font-size:18px">${esc(e.name || 'Candidate')}</b><div class="muted" style="font-size:12px">${esc(e.degree)} ${esc(e.field)} · ${e.cgpa}/${e.cgpa_scale} CGPA · ${e.grad_year}</div></div>
      <div style="text-align:right"><div class="label">Profile Strength</div><div class="stat" style="font-size:34px">${e.profile_score}/100</div></div></div>
      <div class="label" style="margin:16px 0 8px">Academic &amp; Research Strengths</div>${(e.strengths || []).map((s) => `<div class="synth" style="margin:6px 0"><b>${esc(s.title)}</b><div class="muted" style="font-size:12px">${esc(s.detail)}</div></div>`).join("")}
      <div class="label" style="margin:14px 0 8px">Verified Technical Skills</div><div class="chips">${(e.skills || []).slice(0, 14).map((k) => `<span class="pill">${esc(k)}</span>`).join("")}</div>
      ${(e.repos || []).length ? `<div class="label" style="margin:14px 0 8px">Verified GitHub Repositories</div>${e.repos.slice(0, 3).map((r) => `<div class="synth mono" style="margin:6px 0;font-size:12px">${esc(r.name)} <span class="muted">${ic("star", "icon-sm")} ${r.stars} · ${esc(r.language)}</span></div>`).join("")}` : ""}
      ${e.bavarian ? `<div class="synth" style="font-size:12px">German Grade Equiv: <b>≈ ${e.bavarian}</b> (Modified Bavarian Formula).</div>` : ""}`
      : `<div class="muted">Profile Analyst is ingesting your documents…</div>`}</div></div>
  ${S.result ? `<div class="grid g3" style="margin-top:18px">
    <div class="card"><div class="label">Programmes Discovered</div><div class="stat">${S.result.stats.candidates}</div><p class="muted" style="font-size:12px">Across live search &amp; official registries</p></div>
    <div class="card"><div class="label">Live Portals Verified</div><div class="stat">${S.result.stats.verified}</div><p class="muted" style="font-size:12px">${S.result.audit.official}/${S.result.audit.sources_audited} accredited domains</p></div>
    <div class="card"><div class="label">Inter-Agent Messages</div><div class="stat">${S.result.stats.messages_exchanged || (S.messages || []).length}</div><p class="muted" style="font-size:12px">${S.result.stats.retries} retries · ${S.result.stats.fallbacks} fallbacks</p></div></div>` : ""}`;
}

function critHTML(o) {
  return (o.matrix || []).map((x) => `<div class="mx ${x.status}"><b>${ICON[x.status]}</b><div><b>${esc(x.label)}</b><div class="muted">${esc(x.detail)}</div></div></div>`).join("");
}

function citeLine(o) {
  const c = o.citation || {};
  return `<div class="cite">${c.ok ? `<span class="pill green">HTTP ${c.status} · verified ${esc(c.fetched_at)}</span>` : `<span class="pill amber">unverified · ${esc(c.error || "unreachable")}</span>`}
    ${c.archived ? '<span class="pill amber">archived snapshot</span>' : ""} <a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.url)}</a>${c.sha256 ? `<div>sha256: ${esc(c.sha256.slice(0, 16))}…</div>` : ""}</div>`;
}

function vMatches(S) {
  const r = S.result;
  if (!r) return `<div class="empty card"><h2>No matches evaluated yet</h2><p>Deploy the agent swarm to discover and verify scholarships.</p><a class="btn primary" href="#profile">Go to Profile Setup</a></div>`;
  const countries = [...new Set(r.top5.map((o) => o.country).filter(Boolean))];
  const list = S.showAll ? r.candidates : r.top5;
  const shown = list.filter((o) => S.filter === "all" || o.country === S.filter);

  const card = (o) => `<div class="card match"><div style="display:flex;justify-content:space-between;gap:14px">
    <div><div class="pill green">${o.rank ? "RANK #" + o.rank : "DISCOVERY"}${o.rank === 1 ? " · TOP RECOMMENDATION" : ""}</div>
      <div class="muted" style="font-size:12px;margin:8px 0 2px">${esc(o.provider)} · ${esc(o.country)}</div><h2 style="font-size:24px">${esc(o.name)}</h2>
      <div style="margin:8px 0"><span class="pill green">${o.funding === "full" ? "Fully funded" : esc(o.funding)}</span> ${o.deadline_text ? `<span class="pill red" title="${esc(o.deadline_text)}">${ic("clock", "icon-sm")} Deadline: ${esc(o.deadline_text.slice(0, 60))}</span>` : '<span class="pill">Check official portal for deadlines</span>'}</div></div>
    <div class="score" style="--p:${o.score}"><b>${o.score}%</b></div></div>
    <p class="muted" style="font-size:13px">${esc(o.funding_summary)}</p>
    ${o.deadline_text ? `<div class="mx action" style="margin:8px 0"><b>${ic("clock", "icon-action")}</b><div><b>Verified Deadline Evidence</b><div class="muted">“${esc(o.deadline_text.slice(0, 220))}”</div></div></div>` : ""}
    ${o.synthesis ? `<div class="synth"><b>Swarm Match Analysis</b><div style="margin-top:4px">${esc(o.synthesis)}</div></div>` : ""}
    <div class="label">Eligibility Matrix · ${(o.criteria || {}).met || 0}/${(o.criteria || {}).total || 0} met</div><div class="matrix">${critHTML(o)}</div>
    ${(o.page_requirements || []).length ? `<div class="label">Requirements Verified on Official Page</div><ul style="font-size:13px">${o.page_requirements.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
    <div class="muted" style="font-size:13px"><b>Application Procedure:</b> ${esc(o.how_to_apply || "See the official portal.")}</div>
    <div style="display:flex;justify-content:space-between;align-items:flex-end;gap:12px;margin-top:12px">${citeLine(o)}
      <button class="btn primary sm" data-draft="${esc(o.id)}">${ic("pen", "icon-sm")} Draft Statement of Purpose</button></div></div>`;

  const p = r.profile || {};
  return `<div class="head"><div><span class="pill green">SWARM RUN #${esc(r.run_id)} · ${r.stats.live ? (r.stats.verified ? "LIVE-VERIFIED" : "PORTALS UNREACHABLE") : "OFFLINE MODE"}</span>
    <h1 class="page-t">Top ${r.top5.length} Verified Scholarships</h1><p class="muted">Discovered and audited by the six-agent swarm for ${esc(p.name || 'Candidate')} (${esc(p.degree)} ${esc(p.field)}, ${p.cgpa}/${p.cgpa_scale} CGPA).</p></div>
    <div class="card" style="padding:12px 18px"><div class="label">Official Portals Audited</div><div class="stat" style="font-size:30px">${r.audit.sources_audited}</div></div></div>
  ${r.audit.live_verified === 0 ? `<div class="mandate"><b>Notice:</b> ${esc(r.audit.note)} Always confirm details on the linked official page.</div>` : ""}
  <div class="flt"><button class="chip ${S.filter === "all" ? "on" : ""}" data-flt="all">All Destinations</button>${countries.map((c) => `<button class="chip ${S.filter === c ? "on" : ""}" data-flt="${esc(c)}">${esc(c)}</button>`).join("")}
    <label class="chip" style="margin-left:auto"><input type="checkbox" id="showAll" ${S.showAll ? "checked" : ""}> Show all ${r.candidates.length} discovered</label></div>
  <div class="layout3"><div>${shown.map((o) => card(o)).join("") || '<div class="empty">No matches found for this destination filter.</div>'}</div>
  <div><div class="card" style="margin-bottom:14px"><div class="label">Profile Summary</div><b style="font-size:17px;display:block;margin-top:8px">${esc(p.name || 'Candidate')}</b>
    <div class="muted" style="font-size:12px">${esc(p.degree)} ${esc(p.field)} · Class of ${p.grad_year}</div>
    <div class="two" style="margin-top:12px"><div class="synth"><div class="label">Cumulative GPA</div><b>${p.cgpa} / ${p.cgpa_scale}</b></div><div class="synth"><div class="label">German Equiv</div><b>${p.bavarian ?? "N/A"}</b></div></div>
    <div class="muted" style="font-size:12px">Skills: ${esc((p.skills || []).slice(0, 8).join(", "))}</div><a class="btn sm" style="margin-top:10px" href="#profile">${ic("user", "icon-sm")} Edit Profile</a></div>
  <div class="card" style="margin-bottom:14px"><div class="label">Actionable Profile Enhancements</div>
    ${p.ielts_status !== "have" ? '<div class="synth"><b>Official Language Score (IELTS/TOEFL)</b><div class="muted" style="font-size:12px">Most funded programs require official proof of English proficiency.</div></div>' : ""}
    ${!p.github ? '<div class="synth"><b>Public Technical Portfolio</b><div class="muted" style="font-size:12px">Adding your GitHub gives concrete evidence of project expertise.</div></div>' : ""}
    ${!p.transcript_text ? '<div class="synth"><b>Official Transcripts</b><div class="muted" style="font-size:12px">Upload transcripts to substantiate course-specific achievements.</div></div>' : ""}
    <div class="synth"><b>Academic References</b><div class="muted" style="font-size:12px">Most competitive programs mandate 2-3 faculty letters of recommendation.</div></div></div>
  <div class="card"><div class="label">ScholarSwarm Standards</div><ul style="font-size:13px;padding-left:18px"><li>Only accredited institutional &amp; government domains</li><li>Every match carries URL, HTTP status, fetch time, and sha256 hash</li><li>Zero hallucinated publications or credentials</li><li>Applications are never submitted on your behalf</li></ul></div></div></div>`;
}

function mdToHtml(text) {
  const out = [];
  for (const line of (text || "").split("\n")) {
    const t = line.trim();
    if (!t) continue;
    if (t.startsWith("# ")) out.push(`<h1>${esc(t.slice(2))}</h1>`);
    else if (/^applicant:/i.test(t)) out.push(`<div class="meta">${esc(t)}</div>`);
    else if (/^\[ACTION REQUIRED:/i.test(t)) out.push(`<div class="action" contenteditable="false">${esc(t)}</div>`);
    else out.push(`<p>${esc(t).replace(/\[ACTION REQUIRED:[^\]]*\]/g, (m) => `<mark class="action" style="padding:1px 6px">${m}</mark>`).replace(/`([^`]+)`/g, "<code>$1</code>")}</p>`);
  }
  return out.join("");
}

function vDraft(S) {
  const r = S.result;
  if (!r || !r.draft || !r.draft.text) return `<div class="empty card"><h2>No draft synthesized yet</h2><p>Run the swarm and select an opportunity to generate your Statement of Purpose.</p><a class="btn primary" href="#profile">Go to Profile Setup</a></div>`;
  const d = S.draft || r.draft;
  const checks = d.draft_checks || r.audit.draft_checks || [];
  return `<div class="mandate"><b>GROUNDED SYNTHESIS MODE</b> — Prepared by Application Writer. Every claim is cross-verified against your documents. Review before submitting to portals.</div>
  <div class="card" style="margin-bottom:16px"><div class="head" style="margin:0"><div><span class="pill green">DOCUMENT SYNTHESIS · AGENT #06${d.source === "llm" ? " · CLOUD LLM" : " · STRUCTURED SYNTHESIS"}</span>
    <h2 style="font-size:26px;margin-top:8px">Statement of Purpose</h2><div class="muted" style="font-size:13px">Target: ${esc(d.opportunity_name)} · ${esc(d.provider)}</div></div>
    <div class="row"><select id="draftSel" class="chip">${(r.top5.concat(r.candidates.filter((c) => !r.top5.includes(c)))).map((o) => `<option value="${esc(o.id)}" ${o.id === d.opportunity_id ? "selected" : ""}>${esc(o.name.slice(0, 44))}</option>`).join("")}</select>
    <button class="btn" id="regen">${ic("refresh")} Regenerate</button><button class="btn" id="copyTxt">${ic("copy")} Copy Text</button><button class="btn" id="dlPdf">${ic("filePdf")} PDF</button><button class="btn primary" id="dlDocx">${ic("fileDocx")} Word (.docx)</button></div></div></div>
  <div class="layout3"><div><div class="editor" id="editor" contenteditable="true" spellcheck="true">${mdToHtml(d.text)}</div>
    <div class="muted mono" style="font-size:11px;margin-top:8px">${d.word_count} words · ${(d.placeholders || []).length} action items require personal input · edit freely</div></div>
  <div><div class="card" style="margin-bottom:14px"><div class="label">Source Critic · Anti-Hallucination Audit</div>
    ${checks.length ? checks.map((c) => `<div class="mx ${c.status === "verified" ? "met" : c.status === "flagged" ? "unmet" : "action"}" style="margin:8px 0"><b>${c.status === "verified" ? ICON.met : c.status === "flagged" ? ICON.unmet : ICON.action}</b><div><b>${esc(c.claim)}</b><div class="muted">${esc(c.detail)}</div></div></div>`).join("") : '<p class="muted" style="font-size:13px">No checkable credential claims detected.</p>'}</div>
  <div class="card"><div class="label">Zero Hallucination Guarantee</div><p class="muted" style="font-size:13px">Every grade, project name, and technical skill is cross-referenced with your uploaded documents. Missing institutional facts are preserved as <b>ACTION REQUIRED</b> prompts.</p></div></div></div>`;
}

function vSources(S) {
  const r = S.result;
  if (!r) return `<div class="empty card"><h2>Official Source Ledger</h2><p>Deploy the agent swarm to view live verified institutional sources.</p><a class="btn primary" href="#profile">Go to Profile Setup</a></div>`;
  return `<div class="head"><div><span class="pill green">INSTITUTIONAL LEDGER</span><h1 class="page-t">Sources &amp; Live Verification</h1>
    <p class="muted">${r.audit.live_verified}/${r.audit.sources_audited} pages fetched &amp; verified live · 100% accredited official domains.</p></div></div>
  <div class="card" style="overflow:auto"><table><thead><tr><th>Programme &amp; Provider</th><th>Country</th><th>Official URL</th><th>HTTP Status</th><th>Verification Timestamp</th><th>Content SHA-256</th></tr></thead><tbody>
  ${r.candidates.map((o) => `<tr><td><b>${esc(o.name)}</b><div class="muted">${esc(o.provider)}</div></td><td>${esc(o.country)}</td><td class="cite"><a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.url)}</a></td>
    <td>${o.citation && o.citation.ok ? `<span class="pill green">HTTP ${o.citation.status}</span>` : `<span class="pill amber">unverified</span>`}${o.citation && o.citation.fallback_used ? ' <span class="pill">mirror</span>' : ""}</td>
    <td class="cite">${esc(o.citation ? o.citation.fetched_at : "")}</td><td class="cite">${esc((o.citation && o.citation.sha256 ? o.citation.sha256 : "").slice(0, 16))}…</td></tr>`).join("")}</tbody></table></div>`;
}
