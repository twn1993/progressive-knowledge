---
name: progressive-knowledge
description: Set up a progressive knowledge layer for a long-running project: generate a root AGENTS.md (auto-injected by pi), a docs/ state and session tree, and runnable mechanical checks; define what to write, how to write it, what to read, and how to keep context cost low. Use for new projects, undocumented existing projects, or workflows that lose state between sessions (the agent keeps asking "where were we?"). Also use when asked to set up AGENTS.md, project memory, handoff notes, docs structure, or cross-session continuity.
metadata:
  version: "1.0"
---

# Progressive knowledge layer

Goal: the next session should get up to speed in **~1.5k tokens** instead of re-reading the project.
You are **installing** the structure, not filling it.

## When to use / when not

| Use | Don't |
|---|---|
| Work spans sessions, days, or people | A task that ends in one answer |
| Existing project with no state or session record | An equivalent structure already exists (read its entry first; patch gaps only) |
| Large project, many docs, agent keeps editing the wrong place | Pure conversation with no deliverable |

## Procedure (four steps, in order; each can stop cleanly)

### 1. Recon (≤12 tool calls, read-only)

Take only what you need:

1. `ls` the root + existing `README*` → what this work is, what the deliverable is.
2. Build/run entry points: `Makefile` / `package.json` / `pyproject.toml` / `*.sh` / CI config (names and first screen only).
3. Irreversible operations: data directories, generated artifacts, publishing scripts, shared drives.
4. Machine capability: compiler / simulator / credentials / network.
5. Unit of work: one feature / one case / one chapter / one experiment / one deliverable.

Produce four sentences (they go into `AGENTS.md`, not the report): deliverable / irreversible operations / what cannot be verified here / unit of work.

### 2. Write the root `AGENTS.md` (≤120 lines)

Use `templates/AGENTS.md.tmpl`; **keep the section structure**, replace only `<...>`:

- Keep `## 0. Opening (required)`: read `docs/STATE.json` → last 3 lines of the session index → then open one document. The entry starts the session; it does not remember it.
- Never write commit hashes, uncommitted counts, file line counts, or progress percentages (they go stale within a week).
- If `AGENTS.md` already exists: **do not overwrite**. Read it, add only missing sections; if it conflicts, stop and ask.

### 3. Create `docs/` (the only place to write)

```bash
mkdir -p docs/_sessions docs/<topic>
```

In order, using `templates/`:

| # | File | Template |
|---|---|---|
| 1 | `docs/STATE.json` (single state pointer, a projection) | `STATE.json.tmpl` |
| 2 | `docs/_sessions/INDEX.md` | `session-INDEX.md.tmpl` |
| 3 | `docs/_sessions/<date>_bootstrap.md` (≤20 lines) | `session.md.tmpl` |
| 4 | `docs/decisions.md` (one row is enough to start) | `decisions.md.tmpl` |
| 5 | `docs/00_INDEX.md` (what each page covers — **no routing**) | `00_INDEX.md.tmpl` |
| 6 | `docs/<topic>/00_INDEX.md` + `01_*.md` (first topic, ≤120 lines) | `00_INDEX.md.tmpl` |

Do not create five topics at once. The second topic waits until it is actually needed.

### 4. Install scripts and get to a clean run

```bash
mkdir -p tools
cp <skill-dir>/scripts/check.py tools/check.py          # zero dependencies; start here
cp <skill-dir>/scripts/audit.py tools/audit.py          # optional: 22 principles + tiers
cp <skill-dir>/scripts/audit.config.json tools/
python tools/check.py .                                  # must be FAIL 0
```

`<skill-dir>` is provided by pi when the skill loads; use the absolute path.
`check.py` verifies: entry exists and size, per-page limits (max and min), headings, links and anchors, `path:line` evidence, volatile values, `STATE.json` fields, session logs, duplicate routing tables, duplicated long sentences.
`audit.py` is the fuller version (`--tier L0|L1|L2`). Either one is enough.

## Five hard rules (while writing)

1. **Keep the three write types apart**: state overwrites (`STATE`), records append (sessions/decisions), knowledge rewrites in place (pending docs).
2. **Admission questions**: could code derive it? does an authority already exist? is it just process? — any "yes" means do not write it.
3. **Evidence is `path:line`**, and the line must exist; when unsure write `UNKNOWN` plus where you looked.
4. **One authority per fact**; everywhere else links. Keep exactly one routing table, in the entry.
5. **Short is also wrong**: a non-index file below the minimum length should be checked for accidental fragmentation.

Details: `references/writing.md`; `references/principles.md` (22 principles). Read them only when judging a case or changing the rules.

## Delivery report (≤10 lines)

1. Files created (path + line count).
2. `tools/check.py .` result: FAIL/WARN counts.
3. Three facts you are unsure about (with `UNKNOWN` reasons).
4. Suggested next unit of work (one sentence).

Do not paste file contents; do not restate this skill.

## Boundaries

- Write only `AGENTS.md`, `docs/**`, `tools/**`; **never modify source code**, delete existing files, or run `git add/commit/checkout/reset`.
- pi injects only the root `AGENTS.md` as project instructions; do not put `AGENTS.md` in subdirectories (it will never be read).
- When reading ≥3 external documents, delegate to a subagent and take back fact cards with sources; batch fetches with `codemode` instead of fetching one by one.
- This skill is an installer: `/reload` when done. Afterwards the workspace runs on `AGENTS.md` + `tools/check.py`; the skill is no longer needed.
