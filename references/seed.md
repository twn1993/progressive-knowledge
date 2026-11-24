# SEED · build a progressive knowledge layer here

> **You (the model) read this file to execute §1–§6, not to summarize it.**
> Outputs: a root `AGENTS.md` (pi injects it automatically), a `docs/` folder (the only place to write), and a runnable `tools/check.py`.
> Principle: **read little, write precisely, verify mechanically.** Do not fill the tree in one pass, and do not copy this file.

---

## 0. Execution contract

| Item | Value |
| --- | --- |
| Allowed writes | only `AGENTS.md`, `docs/**`, `tools/**` under this project root |
| Forbidden | editing source code or existing docs, deleting files, `git add/commit/checkout/reset` |
| Tool budget | recon ≤12 calls; total new files ≤10 (L0 can be 5) |
| On conflict | stop and ask; never guess. Guesses go in as `UNKNOWN` + where you looked |
| Existing `AGENTS.md` | **do not overwrite**: read it, add only missing sections; on conflict stop and let the user choose (overwrite / create `AGENTS.knowledge.md` plus one pointer line) |
| After bootstrap | read only `AGENTS.md` → `docs/STATE.json` → last 3 lines of `docs/_sessions/INDEX.md` → one body page |

**Why this is not optional**: effective context is much smaller than the advertised size; status written into docs goes stale within days; LLM summaries lose details (controlled tests retain ≤16% of recurring details). Therefore: **state on disk, pointers in the entry, line numbers for evidence**.

---

## 1. Recon (≤12 calls, read-only)

Take these in order and stop when you have enough:

1. `ls` the root + existing `README*` → what this work is and what the deliverable is.
2. Find build/run entry points: `Makefile` / `package.json` / `pyproject.toml` / `*.sh` / CI config (file names and first screen only).
3. Identify irreversible operations: data directories, generated artifacts, publishing scripts, shared drives.
4. Determine what this machine cannot verify: compiler, simulator, credentials, network.
5. Decide the **unit of work**: one feature / one case / one chapter / one experiment / one deliverable.

Produce four sentences (they go into `AGENTS.md`, not into the report): deliverable / irreversible operations / what cannot be verified / unit of work.

> pi specific: **only the root `AGENTS.md` is injected** as project instructions. Do not put `AGENTS.md` in subdirectories (pi will not read it; it becomes a dead file). Put sub-domain rules in `docs/` and route to them from the entry.

---

## 2. Write `AGENTS.md` (template A at the end, ≤120 lines)

Rules:

- **Keep the structure**, replace `<...>` placeholders; do not add sections (each extra section pushes something else out).
- Never write: commit hashes, uncommitted counts, file line counts, progress percentages, "currently N items".
- Only write: structural facts (which blocks exist, what is read-only), routing (I want… → read which), hard constraints, closing obligations.
- For a very small project (one-off, under a week), trim template A to §0–§5.

---

## 3. Create `docs/` (the only place to write)

```bash
mkdir -p docs/_sessions docs/<topic1> [docs/<topic2>]
```

Write in this order; you can stop after any step:

| # | File | Content | Template |
| --- | --- | --- | --- |
| 1 | `docs/STATE.json` | state pointer (a projection) | B |
| 2 | `docs/_sessions/INDEX.md` | header + one bootstrap row | C2 |
| 3 | `docs/_sessions/<date>_bootstrap.md` | what this session did (≤20 lines) | C1 |
| 4 | `docs/decisions.md` | decision ledger (one row is enough) | C3 |
| 5 | `docs/00_INDEX.md` | what each page covers (**no routing**) | C4 |
| 6 | `docs/<topic1>/00_INDEX.md` + `01_*.md` | first topic, ≤120 lines | C4 |
| 7 | `tools/check.py` | mechanical self-check (copy from `scripts/check.py`) | — |

**Do not** write five topics. The second topic waits until it is actually needed.

---

## 4. How to read and write afterwards (rules for the next session)

### Read (≤1.5k tokens cold start)

```
1 Read AGENTS.md (the entry only, not the whole docs tree)
2 Read docs/STATE.json (the only state)
3 Read the last 3 lines of docs/_sessions/INDEX.md
4 Follow next_action or the routing table; open exactly one body page
5 STATE.last_session ≠ newest session file ⇒ rebuild STATE from logs before working
6 STATE.derived_at too old ⇒ run commands first
```

Never read `docs/` linearly; never load several body pages at once. pi specific: when you need ≥3 external documents, delegate to a subagent and take back fact cards with sources; batch fetches with `codemode` rather than fetching one at a time.

### Write (three kinds, different rules)

| Kind | Location | Mode | Old content |
| --- | --- | --- | --- |
| State | `docs/STATE.json` | overwrite | replaceable (the truth is in logs) |
| Record | `_sessions/`, `decisions.md`, `opens[]` | **append only** | never edit; closing changes a status field and keeps the row |
| Knowledge | `docs/<topic>/*.md` | **rewrite in place** | delete outdated text; no history sections |

**Three admission questions** (any "yes" means do not write): could code or data derive it? does an authority already exist? is it just this session's process?

**How much**: entry ≤120 lines; one body page ≤120; session log ≤20; one decision = one row; a non-index page under 15 lines needs a fragmentation check.

**Three hard requirements**: evidence as `path:line` that really exists; no volatile values (write how to fetch them); one authority per fact (everything else links).

---

## 5. Self-check (required; PASS is the definition of done)

```bash
python tools/check.py .
```

It checks: entry presence and size, per-page line counts, headings, relative links and anchors, `path:line` existence, volatile values, `STATE.json` fields, session log size, duplicate routing tables, duplicated long sentences.

- Any `FAIL`: fix until none remain (all are minute-level fixes).
- `WARN` only: read each one; keep it if you can justify it, otherwise fix it.
- If the project already has a stronger checker (for example `scripts/audit.py`), use it and make `check.py` a one-line forwarder.

---

## 6. Delivery report (≤10 lines, to the user)

1. Files created (path + line count).
2. `check.py` result: FAIL/WARN counts.
3. Three facts you are unsure about (with `UNKNOWN` reasons).
4. Suggested next unit of work (one sentence).

Do not paste file contents; do not restate this seed.

---

# Appendix A · `AGENTS.md` template (≤120 lines, keep the structure)

```markdown
# <PROJECT> · agent contract

> This page is the **only entry**. After reading, route via §4 to **one** page under `docs/`; do not read in order.
> State lives only in `docs/STATE.json`; this page contains no changing values.

## 0. Opening (required, ≤2 minutes)

After this page is injected, do this in order before any work:

1. Read `docs/STATE.json` (the only state).
2. Read the last 3 lines of `docs/_sessions/INDEX.md`.
3. `last_session` ≠ newest session file ⇒ rebuild STATE from logs first; `derived_at` too old ⇒ run `commands` first.
4. Follow `next_action` or §4; open exactly one body page.

## 1. What this is

<One sentence: what this work is plus the deliverable. No progress.>

## 2. Capability boundary

| This machine can | This machine cannot |
| --- | --- |
| <read/edit code, organize, compare> | <build / simulate / run on hardware / reach the intranet> |

⇒ Never conclude "passes / works" here; give `[unverified]` plus a verification checklist (§6).

## 3. Irreversible / high-risk (specific to this project)

| # | Never do | Consequence |
| --- | --- | --- |
| C1 | <delete/overwrite the data directory> | <cannot be regenerated> |
| C2 | <publish / send externally> | <cannot be recalled> |
| C3 | <edit a shared sheet / shared drive> | <visible to others, no rollback> |
| C4 | Overwrite rows already appended in `docs/_sessions/` | Session logs are append-only; editing history erases the state source |

## 4. What to read (intent routing)

| I want… | Read under `docs/` |
| --- | --- |
| <most common task> | `<domain>/01_<topic>.md` |
| <second most common> | `<domain>/02_<topic>.md` |
| <third> | `<domain>/03_<topic>.md` |
| Why we chose this / what was rejected | `decisions.md` |
| Where we are / what is next | `STATE.json` |
| Where the last session stopped | last 3 lines of `_sessions/INDEX.md` |

## 5. What to write (three kinds)

- **State** → `docs/STATE.json` (overwrite; it is a projection)
- **Record** → `docs/_sessions/`, `decisions.md`, `opens[]` (append only)
- **Knowledge** → `docs/<topic>/*.md` (rewrite in place; delete what is outdated)

Admission questions (any "yes" means do not write): could code derive it? does an authority exist? is it just process?

## 6. Document conventions

- Size, section length, budget: **defined by the constants in `tools/check.py` or `tools/audit.config.json`**, never copied here.
- Exactly three markers: `[verified]` / `[inferred]` / `[unverified]`; upgrades require new evidence.
- Evidence is `path:line` relative to this project; the line must exist.
- One authority per fact; living documents carry no history.

## 7. Closing obligations (done is not done)

1. Run `python tools/check.py .`; no new FAIL.
2. Create `docs/_sessions/<date>_<sid>.md` (≤20 lines) and append one row to `INDEX.md`.
3. Update `docs/STATE.json`: `opens` / `next_action` / `updated_at` / `last_session`.
4. New approach, rejected approach, failed route → one row in `docs/decisions.md`.
5. New evidence → write it back to the body page and upgrade the marker (with a line reference).

## 8. Never

- Never write volatile values here or in indexes (commit hashes, uncommitted counts, line counts, progress percentages).
- Never read `docs/` in order; never put process diaries into body pages.
- Never claim "passes / works" without verification.
```

---

# Appendix B · `docs/STATE.json` (the only state)

```json
{
  "schema_version": 1,
  "updated_at": "2026-01-01T10:00:00+08:00",
  "last_session": "2026-01-01_bootstrap",
  "phase": "<phase name>",
  "derived_at": "2026-01-01T09:50:00+08:00",
  "commands": {
    "repo_state": "<a command or procedure that re-derives current state>",
    "artifacts": "<a command that checks whether outputs exist>"
  },
  "opens": [
    { "id": "O-001", "item": "<where it is stuck>", "status": "open",
      "next_action": "<one directly executable action>", "evidence": "<path:line>" }
  ],
  "next_action": "<the single thing this session should do>"
}
```

Rules: `status ∈ open|blocked|done|dropped`; `done` rows stay; STATE can be rebuilt from `_sessions/` + `decisions.md` at any time; keep it within one screen, never store history.

---

# Appendix C · the other three templates

**C1 session log** (≤20 lines)

```markdown
# <date> · <sid>

- **Goal**: <one sentence>
- **Done**: <1–3 results, no process>
- **Files touched**: `<path>`, `<path>`
- **Ran**: <nothing / static checks only / on hardware: command + result>
- **Stuck at**: <one sentence; "no" if none>
- **Next command**: `<one copy-pasteable line>`
- **Status change**: O-00x open → blocked
```

**C2 `INDEX.md`** (append only)

```markdown
# Session index (append-only)

| Date | sid | One line | Status change |
| --- | --- | --- | --- |
| <date> | bootstrap | Created entry and state | initialized |
```

**C3 `decisions.md`** (closed status set)

```markdown
# Decision ledger

## Contents

1. [<topic>](#1-topic) · 2. [Pending](#2-pending)

## 1. <topic>

| # | Decision | Status | Reason | Evidence |
| --- | --- | --- | --- | --- |
| D1 | <approach> | **adopted** | <why> | `<path:line>` |
| D2 | <alternative> | **rejected** | <why not> | `<path:line>` |

## 2. Pending

| # | Pending | Blocked on |
| --- | --- | --- |
| Q1 | <question> | <what is missing> |
```

**C4 index or topic page header** (any page ≥30 lines needs contents)

```markdown
# <title>

> One sentence: the question this page answers. Not a routing table (routing lives only in `AGENTS.md`).

## Contents

- [1. <section>](#1-section)
- [2. <section>](#2-section)
- [3. <section>](#3-section)

## 1. <section>

<Conclusion first; evidence as `path:line`; inference marked `[inferred]`. Keep a section ≤25 lines.>
```

---

# Appendix D · Ten lessons: what keeps them alive

**Why this table exists**: this file is read once and then archived. Lessons cannot survive on memory; each must land in a carrier.

| Carrier | When it acts | Who reads |
| --- | --- | --- |
| **Mechanical checks** (`tools/check.py`, `scripts/audit.py`) | at every close, automatically | the machine |
| **Entry prohibitions** (`AGENTS.md`) | every session, injected | the model |
| **Decision ledger** (`decisions.md` D0 + a link to this file) | only when changing the structure | a human |

| # | Lesson | Carrier | How it still works without this file | Symptom when it fails |
| --- | --- | --- | --- | --- |
| 1 | Status in the entry expires within a week | **mechanical**: volatile-value regex | `check.py` fails outright | entry numbers disagree with reality |
| 2 | The same fact in two places diverges | **mechanical**: duplicated long sentences | `check.py` warns | two places, two conclusions |
| 3 | Two routing tables evolve apart | **mechanical**: duplicate routing detection | `check.py` warns | entry and index point at different pages |
| 4 | A cap without a floor shreds topics | **mechanical**: `MIN_LINES` | `check.py` warns | one topic becomes four 8-line pages |
| 5 | "Remember to update" never happens | **mechanical + entry**: check must run, §7 closing | the checklist is injected | empty session log, stale STATE |
| 6 | State scattered across prose cannot resume | **mechanical**: STATE fields + entry §0 | the protocol reads STATE first | every session asks "where were we?" |
| 7 | No reconciliation after a crash | **mechanical**: `last_session` | checker warns | the session starts from a stale state |
| 8 | Summaries replace originals, details vanish | **entry**: evidence as `path:line`, keep originals | §6 conventions + P22 | conclusions cannot be traced to a paragraph |
| 9 | Hand-written line numbers are invented | **mechanical**: line-range check | `check.py` fails outright | `:42` points into a 4-line file |
| 10 | Filling the tree at once leaves 90% unread | **bootstrap only** (this file) | no runtime need: it matters on day one | 20 pages created, none opened again |

**Conclusion**: lessons 1–9 have runtime carriers; lesson 10 is a bootstrap-time behavior. "Nobody reads this file later" is the design, provided §3 was completed.

**Suggested archive**: after bootstrap, move this file to `docs/_archive/SEED.md` and add one row to `docs/decisions.md`:

```markdown
| D0 | Adopt the entry + state + sessions + decisions knowledge layer | **adopted** | Rationale and trade-offs in `_archive/SEED.md` | `docs/_archive/SEED.md` |
```

Link only. **Do not copy the ten lessons into the entry** — they would consume the resident budget and go stale anyway.
