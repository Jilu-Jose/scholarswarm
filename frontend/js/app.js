const DEFAULT_PROFILE = {
  name: "", degree: "B.Tech", field: "", cgpa: 8.0, cgpa_scale: 10, grad_year: 2026,
  location: "", nationality: "India", github: "", linkedin: "", extra_urls: [],
  destinations: ["Germany", "Canada"], target_degree: "masters", research_interest: "",
  funding_need: "full", ielts_status: "none", ielts_score: null, work_years: 0,
  resume_text: "", transcript_text: "", skills: []
};

const S = {
  profile: { ...DEFAULT_PROFILE }, uploads: {}, runId: null, events: [], messages: [],
  agents: [], enriched: null, result: null, finished: false, elapsed: "", filter: "all",
  showAll: false, draft: null, health: null, es: null, view: "overview", swarmTab: "messages"
};

try {
  const saved = JSON.parse(localStorage.getItem("ss_profile") || "null");
  if (saved) {
    // If it was the old demo profile, clear it out
    if (saved.name === "Rahul Sharma" || saved.name === "Ananya Verma") {
      localStorage.removeItem("ss_profile");
    } else {
      S.profile = { ...DEFAULT_PROFILE, ...saved };
    }
  }
} catch (e) {}

const $ = (id) => document.getElementById(id);
const toast = (m) => {
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = m;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2800);
};

function readForm() {
  if (!$("f_name")) return;
  const g = (id) => $(id) ? $(id).value : "";
  const p = S.profile;
  Object.assign(p, {
    name: g("f_name"),
    field: g("f_field"),
    cgpa: parseFloat(g("f_cgpa")) || 0,
    cgpa_scale: parseFloat(g("f_scale")),
    grad_year: parseInt(g("f_year")) || 2026,
    work_years: parseFloat(g("f_work")) || 0,
    location: g("f_loc"),
    github: g("f_github").trim(),
    linkedin: g("f_linkedin").trim(),
    extra_urls: g("f_extra").split(",").map((x) => x.trim()).filter(Boolean),
    research_interest: g("f_interest"),
    funding_need: g("f_funding"),
    ielts_status: g("f_ielts_status"),
    ielts_score: g("f_ielts") === "" ? null : parseFloat(g("f_ielts"))
  });
  if (p.linkedin && !p.extra_urls.includes(p.linkedin) && p.linkedin.startsWith("http")) {
    p.extra_urls = [...p.extra_urls, p.linkedin];
  }
  localStorage.setItem("ss_profile", JSON.stringify(p));
  if ($("uName")) $("uName").textContent = p.name || "Student";
  if ($("uAv")) $("uAv").textContent = (p.name || "S")[0].toUpperCase();
}

function parseHash() {
  const [v, q] = (location.hash.slice(1) || "overview").split("?");
  return { v: v || "overview", q: new URLSearchParams(q || "") };
}

function render() {
  const { v } = parseHash();
  S.view = v;
  document.querySelectorAll(".nav-i").forEach((a) => a.classList.toggle("on", a.dataset.v === v));
  const map = { overview: vOverview, profile: vProfile, swarm: vSwarm, matches: vMatches, draft: vDraft, sources: vSources };
  const keepScroll = v === "swarm" && $("term") ? $("term").scrollTop : null;
  const atBottom = keepScroll !== null && $("term").scrollHeight - $("term").scrollTop - $("term").clientHeight < 50;

  $("view").innerHTML = (map[v] || vOverview)(S);

  if (v === "swarm" && $("term") && (atBottom || keepScroll === null)) {
    $("term").scrollTop = $("term").scrollHeight;
  }
  bind(v);
  if ($("uName")) $("uName").textContent = S.profile.name || "Student";
  if ($("uAv")) $("uAv").textContent = (S.profile.name || "S")[0].toUpperCase();
}

function bind(v) {
  if (v === "profile") {
    document.querySelectorAll("#view input, #view select").forEach((el) => {
      if (el.type !== "file") el.addEventListener("change", readForm);
    });
    if ($("destChips")) {
      $("destChips").onclick = (e) => {
        const d = e.target.dataset.dest;
        if (!d) return;
        readForm();
        const a = S.profile.destinations;
        S.profile.destinations = a.includes(d) ? a.filter((x) => x !== d) : [...a, d];
        render();
      };
    }
    if ($("degChips")) {
      $("degChips").onclick = (e) => {
        const d = e.target.dataset.deg;
        if (!d) return;
        readForm();
        S.profile.target_degree = d;
        render();
      };
    }
    ["resume", "transcript"].forEach((k) => {
      if ($("up_" + k)) {
        $("up_" + k).onchange = async (e) => {
          const f = e.target.files[0];
          if (!f) return;
          readForm();
          try {
            toast(`Parsing ${f.name}…`);
            const r = await upload(k, f);
            S.uploads[k] = r;
            S.profile[k === "resume" ? "resume_text" : "transcript_text"] = r.text;
            if (r.skills && r.skills.length) {
              S.profile.skills = [...new Set([...S.profile.skills, ...r.skills])];
            }
            if (r.cgpa && (!S.profile.cgpa || k === "transcript")) {
              S.profile.cgpa = r.cgpa;
              S.profile.cgpa_scale = r.cgpa_scale;
            }
            toast(`Parsed ${f.name}: extracted ${r.skills.length} skills${r.cgpa ? ` and CGPA ${r.cgpa}` : ""}`);
            render();
          } catch (err) {
            toast("Upload failed: " + err.message);
          }
        };
      }
    });
    if ($("saveDraft")) $("saveDraft").onclick = () => { readForm(); toast("Profile saved in this browser"); };
    if ($("deploy")) $("deploy").onclick = deploy;
  }
  if (v === "swarm") {
    document.querySelectorAll("[data-stab]").forEach((b) => {
      b.onclick = () => {
        S.swarmTab = b.dataset.stab;
        render();
      };
    });
  }
  if (v === "matches") {
    document.querySelectorAll("[data-flt]").forEach((b) => (b.onclick = () => { S.filter = b.dataset.flt; render(); }));
    if ($("showAll")) $("showAll").onchange = (e) => { S.showAll = e.target.checked; render(); };
    document.querySelectorAll("[data-draft]").forEach((b) => (b.onclick = () => makeDraft(b.dataset.draft)));
  }
  if (v === "draft" && $("regen")) {
    $("regen").onclick = () => makeDraft($("draftSel").value);
    $("draftSel").onchange = () => makeDraft($("draftSel").value);
    $("copyTxt").onclick = () => { navigator.clipboard.writeText($("editor").innerText); toast("Copied statement to clipboard"); };
    $("dlDocx").onclick = () => download("docx", "Statement of Purpose", $("editor").innerText).catch((e) => toast(e.message));
    $("dlPdf").onclick = () => download("pdf", "Statement of Purpose", $("editor").innerText).catch((e) => toast(e.message));
  }
}

async function makeDraft(oppId) {
  toast("Application Writer synthesizing Statement of Purpose…");
  try {
    S.draft = await jpost("/api/draft", { run_id: S.runId, opportunity_id: oppId });
    location.hash = "#draft";
    render();
  } catch (e) {
    toast("Draft failed: " + e.message);
  }
}

async function deploy() {
  readForm();
  const p = S.profile;
  if (!p.name || !p.cgpa) return toast("Please provide your name and CGPA");
  if (!p.destinations.length) return toast("Select at least one destination country");
  if (S.es) S.es.close();

  S.events = [];
  S.messages = [];
  S.agents = [];
  S.enriched = null;
  S.result = null;
  S.finished = false;
  S.draft = null;
  S.filter = "all";

  try {
    const { run_id } = await jpost("/api/swarm/start", p);
    S.runId = run_id;
    location.hash = "#swarm";
    listen(run_id);
  } catch (e) {
    toast("Could not start swarm: " + e.message + " (is the backend running?)");
  }
}

function listen(runId) {
  const es = new EventSource(API + `/api/swarm/${runId}/stream`);
  S.es = es;
  let pending = false;
  const schedule = () => {
    if (pending) return;
    pending = true;
    setTimeout(() => {
      pending = false;
      if (S.view === "swarm") render();
    }, 280);
  };

  es.onmessage = async (m) => {
    const ev = JSON.parse(m.data);
    if (ev.type === "agent") {
      const i = S.agents.findIndex((a) => a.id === ev.id);
      if (i >= 0) S.agents[i] = ev; else S.agents.push(ev);
    } else if (ev.type === "profile") {
      S.enriched = ev.data;
    } else if (ev.type === "message") {
      S.messages.push(ev);
      S.elapsed = ev.t;
    } else if (ev.type === "log") {
      S.events.push(ev);
      S.elapsed = ev.t;
    } else if (ev.type === "result" || ev.type === "error") {
      es.close();
      S.finished = true;
      try {
        S.result = await jget(`/api/swarm/${runId}/result`);
        S.enriched = S.result.profile;
        if (S.result.messages) S.messages = S.result.messages;
      } catch (e) {}
      if ($("agentPill")) $("agentPill").innerHTML = '<span class="dot"></span> swarm complete';
      render();
      return;
    }
    schedule();
  };

  es.onerror = () => {
    if (!S.finished) {
      es.close();
      toast("Lost connection to the backend stream");
    }
  };
}

window.addEventListener("hashchange", () => render());

(async () => {
  try {
    S.health = await jget("/api/health");
  } catch (e) {
    S.health = null;
  }
  render();
})();
