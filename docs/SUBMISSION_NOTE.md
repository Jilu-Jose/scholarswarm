# Short note: experiment and challenge

**Most interesting experiment.** Splitting "who decides" from "who writes". The LLM never decides eligibility: a deterministic rules engine
scores each programme, and the LLM only writes the fit notes and the SOP from the same facts. I also added a Source Critic agent that
checks every CGPA figure, project name and credential claim in the draft against the candidate's own documents, and lets the writer
leave `[ACTION REQUIRED]` placeholders instead of inventing evidence.

**Biggest technical challenge.** Official sites are inconsistent: they time out, move pages, or block bots. The verifier retries, tries
official fallback URLs, then an archive snapshot (clearly labelled), and otherwise marks the result "unverified" rather than pretending.
The curated registry carries only indicative criteria; deadlines are shown only when found on the fetched official page.

**Known limits (please read).** Registry criteria such as minimum CGPA are indicative, not official. Deadlines are extracted from page text
and should be confirmed on the linked page. Live verification needs outbound internet access from wherever the backend runs.

