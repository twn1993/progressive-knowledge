# Demo project · agent contract

> This page is the **only entry**. After reading, route via §4 to **one** page under `docs/`; do not read in order.
> State lives only in `docs/STATE.json`; this page contains no changing values.

## 0. Opening (required, ≤2 minutes)

1. Read `docs/STATE.json` (the only state).
2. Read the last 3 lines of `docs/_sessions/INDEX.md`.
3. `last_session` ≠ newest session file ⇒ rebuild STATE from logs first; `derived_at` too old ⇒ run `commands` first.
4. Follow `next_action` or §4; open exactly one body page.

## 1. What this is

Turn a pile of source material into a checkable conclusion report. The deliverable is the report plus an evidence table; the unit of work is one source → one evidence card.

## 2. Capability boundary

| This machine can | This machine cannot |
| --- | --- |
| read sources, organize, compare | reach internal systems, contact people, re-run the original experiment |

⇒ Never conclude "confirmed" here; give `[unverified]` plus a verification checklist (§6).

## 3. Irreversible / high-risk

| # | Never do | Consequence |
| --- | --- | --- |
| C1 | Overwrite anything under `_sources/` | Originals cannot be regenerated |
| C2 | Copy unredacted material from `_sources/` into a shared folder | Distribution cannot be recalled |
| C3 | Edit a published conclusion without a trace | Downstream already decided on it |
| C4 | Overwrite rows already appended in `docs/_sessions/` | Session logs are append-only; editing history erases the state source |

## 4. What to read (intent routing)

| I want… | Read under `docs/` |
| --- | --- |
| to know what question we answer | `topic/01_brief.md` |
| the evidence cards | `topic/02_evidence.md` |
| why we organized it this way | `decisions.md` |
| where we are / what is next | `STATE.json` |
| where the last session stopped | last 3 lines of `_sessions/INDEX.md` |

## 5. What to write (three kinds)

- **State** → `docs/STATE.json` (overwrite; it is a projection)
- **Record** → `docs/_sessions/`, `decisions.md`, `opens[]` (append only)
- **Knowledge** → the topic pages under `docs/` (rewrite in place; delete what is outdated)

Admission questions (any "yes" means do not write): could the source derive it? does an authority exist? is it just process?

## 6. Document conventions

- Size, section length, budget: defined by the constants in `tools/check.py`, never copied here.
- Exactly three markers: `[verified]` / `[inferred]` / `[unverified]`.
- Evidence is `path:line` relative to this project; the line must exist.
- One authority per fact; living documents carry no history.

## 7. Closing obligations

1. Run `python tools/check.py .`; no new FAIL.
2. Add one file under `docs/_sessions/` named by date and sid (≤20 lines), and append one row to `INDEX.md`.
3. Update `docs/STATE.json`: `opens` / `next_action` / `updated_at` / `last_session`.
4. New approach, rejected approach, failed route → one row in `docs/decisions.md`.
5. New evidence → write it back and upgrade the marker (with a line reference).

## 8. Never

- Never write volatile values here or in indexes (commit hashes, uncommitted counts, line counts, progress percentages).
- Never read `docs/` in order; never put process diaries into body pages.
- Never claim "passes / works" on this machine.
