# How to write (progressive writing guide)

> Reading is "expand from the entry on demand". Writing is "**small to large, pointer to body, increments only**".
> This page covers three things: **what to write, how to write it, what must hold afterwards**. Skeleton and layout are in `bootstrap.md`.

## 0. Separate three kinds of writing (their rules differ)

| Kind | Files | Mode | What happens to old content |
| --- | --- | --- | --- |
| **State** | `STATE.json` | overwrite (it is a projection) | may be replaced; the truth is in logs and can be rebuilt |
| **Record** | `_sessions/`, `decisions.md`, `opens[]` | **append only** | never edit or delete; closing changes a status field and keeps the row |
| **Knowledge** | `docs/<topic>/*.md` | **rewrite in place** | delete or rewrite outdated text; no "previous version" sections |

The most common mistake: treating knowledge as a record (it grows forever), or a record as state (history disappears).

## 1. What to write: three admission questions

Before any sentence goes into a file, ask three questions. **Any "yes" means do not write it**:

1. Could the next session derive it from code, data, or the source text?
2. Does an authority already exist? (then link)
3. Is it just this session's process (what was tried, which files were read)? (process goes to the session log, not the body)

## 2. Where to write: one table

| What you want to keep | Where | Who | When |
| --- | --- | --- | --- |
| How to work in this project (hard rules, prohibitions, boundaries) | entry `AGENTS.md` | human | at bootstrap; when rules change |
| Where we are, what is next, what is blocked | `docs/STATE.json` | executor | at every close |
| What was done this session, where it got stuck, next command | `docs/_sessions/<date>_<sid>.md` | executor | at every close |
| Why we chose this, what was rejected | `docs/decisions.md` | decision maker | when a fork appears |
| Mechanism, how to run, pitfalls of one topic | `docs/<topic>/NN_*.md` | executor | when something is actually understood |
| A task's scope and acceptance criteria | one body page (or an external change folder) | executor | before starting |

**Test**: ask which row it belongs to; if it fits none, it probably should not be written.

## 3. Progressive writing: four actions, three granularities

**Four actions (light to heavy)**

| Action | Use for | Constraint |
| --- | --- | --- |
| **Append** | session logs, decisions, opens | add only; one row per item |
| **Rewrite** | an outdated section in a body page | replace in place; delete the old claim |
| **Create** | a new topic or unit of work | one page answers one question; ≤ `limits.default` |
| **Archive** | a page that no longer applies | move to `_archive/`; live pages stop linking to it |

**Three granularities**

1. **One intent at a time**: while writing a page, answer one question; the second question gets its own page.
2. **Pointer before body**: add the "I want… → read it" row first, even if the page has three lines.
3. **Increments only**: do not rewrite the whole page each time; edit the section that changed.

**Bootstrap rhythm**: L0 four files (entry / STATE / decisions / `_sessions/`) → first topic page → second topic page. **Do not fill the tree in one go.**

## 4. How much (hard limits; numbers live in `tools/audit.config.json`)

| Object | Limit | Note |
| --- | --- | --- |
| Entry | `limits.default` | routing, boundaries, prohibitions, write-back only |
| Body page | `limits.default` | over the cap means split by intent, not delete content |
| Index / inventory / troubleshooting | `limits.index` etc. | exempt categories must be listed in config |
| Section | `section_max_lines` | split the section, or turn it into a table |
| Session log | 20 lines | it is a briefing, not a diary |
| One decision | one table row | reason ≤ 1 sentence; long argument goes to a body page and links |

**The floor is also a constraint**: a non-index page below `min_doc_lines` should be checked for accidental fragmentation.

## 5. Three requirements a machine can check

1. **Evidence resolves**: write `path:line`; the line must exist. When unsure, write `UNKNOWN` and where you looked — never "probably / should be".
2. **No volatile values**: commit hashes, uncommitted counts, file line counts, progress percentages, "currently N" — replace with how to fetch them (a command or a procedure).
3. **One authority per fact**: everywhere else links. If two places both state it, delete one.

Supporting rules: only `[verified]` / `[inferred]` / `[unverified]`; relative links across files; anchors must match real headings.

## 6. What not to write (counter-list)

- Architecture and file paths that code already reveals (they cost resident context and expire).
- Process diaries (which files were read, which commands were run) — keep "conclusion + next command".
- Raw logs and full outputs — give a path or a handle, do not paste.
- A second copy of the same fact, even reworded.
- "The old approach was…" sections — choices belong in the decision ledger.
- Temporary paths, machine-specific absolute paths, personal credentials.

## 7. Self-check after writing (≤2 minutes)

1. Run `python tools/audit.py . --tier <yours>` (or `tools/check.py .`) — no new FAIL.
2. Three questions: will this be used next time? is there a second copy? does the `path:line` resolve?
3. Did this session write a log and update `STATE.last_session` and `next_action`?
4. Do new links and anchors point at real targets?
5. Did process leak into a body page instead of the session log?
