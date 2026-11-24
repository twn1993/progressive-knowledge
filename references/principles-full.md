# 22 principles (long form)

> **Reference only.** Normal bootstrapping reads `principles.md` (the quick table).
> Read this page when you need to decide whether a principle applies, or when changing thresholds.
> Thresholds are still defined only in `audit.config.json`; this page explains why they exist.

## 0. Two premises

### 0.1 Why this layer is needed

A model's **effective context is far smaller than the advertised size** (measured: models advertised at 128K degrade noticeably well before that; remove literal matching and the gap can reach tens of times). And **LLM-summarized compression loses details systematically** (controlled tests retain ~16% of "recurring details"). So the correct move is not "put the history into the window", but:

> **Write state and decisions to disk, and have the agent read only the small slice the index points at.**

These principles turn "the shape of that slice" into checkable clauses.

### 0.2 No git required

| Need | With git | Without git |
| --- | --- | --- |
| What changed last time | `git log` / `git status` | `_sessions/` logs + one `done` row per unit |
| What version this is | commit hash | version number / date / `MANIFEST.md` |
| Rollback | checkout | `_snapshots/YYYY-MM-DD/` copies |
| Parallel safety | branches | one file per session + append-only index (P16) |

The judgments do not change: P04 forbids **hard-coded volatile values**, regardless of where they came from; P15 asks for **a command or a procedure** that re-derives the value.

## A. Entry layer

### P01 · One entry file with a size cap

**Assertion**: exactly one entry file at the workspace root, lines ≤ cap (threshold only in `limits.default`), and it declares itself the only entry.

**Why**: the entry is the fixed cost of every session. Without a cap it becomes a second document set; with several entries they diverge.

**Judgment (mechanical)**: entry exists; line count ≤ cap; the first 10 lines contain "entry / only / read this first".

**Counter-example**: a 300-line entry that overlaps a sub-directory entry; both are "current".

**Exception**: if a tool forces another filename, keep a one-line forwarding file — never two bodies.

### P02 · Intent routing, no linear reading

**Assertion**: the entry contains a "I want… → read which" table with ≥`routing_min_rows` rows, and says explicitly "do not read in order".

**Why**: the retrieval key is an **intent**, not directory order. Linear reading grows with the number of pages; lookup is O(1).

**Judgment (mechanical)**: a table with enough rows and "read / see / →" in it; plus one of "do not read in order / on demand / one page only".

**Counter-example**: an entry that is just a list of directories; a routing table in both the entry and the index (also violates P21).

### P03 · Sub-domain files implement, never relax

**Assertion**: multiple entry files are allowed, but a child file may only **apply** the parent's rules to its directory, must say "stricter is fine, looser is not", and must link back to the parent. The rule body exists once.

**Why**: proximity-scoped rules are right, but they easily fork: parent says "never X", child says "try not to X".

**Judgment (semi-mechanical)**: the script checks that the child references the parent entry; a human checks that "never" did not become "prefer / usually / depends".

**Counter-example**: the same prohibition worded differently at two levels; a child copying the parent's full list instead of linking.

### P04 · Zero volatile facts in the resident layer

**Assertion**: the entry file and top index must not contain values that expire:
commit hashes, version literals, "currently/latest" plus a number, item counts (`×N`, `N items`), file line counts, progress percentages, measured readings.

Only two things are allowed: **structural facts** (topology, responsibilities, dependencies) and **re-derive methods** (a command or a procedure).

**Why**: this is the most frequent death. It is true when written, starts expiring when committed; the first reader who checks stops trusting the whole set. Measured case: an entry recorded "`D×3 + M×5 + ??×6`"; seven days later the tree was clean, and the same numbers were copied into five files — all wrong.

**Judgment (mechanical)**: regex scan of the resident layer; any hit is FAIL:
`HEAD` + hex, `commit … <hex>`, `×N`, `N items + status word`, `status --porcelain` followed by a number, `N commits`, `N files … N lines`, `current/latest/as of + number`, `done N%`.

**Non-code equivalents**: "37 replies received so far", "latest version v2.3.1", "4 chapters left" — all forbidden in the entry.

**Exception**: a structural fact may carry a one-time verification date ("verified 2026-01"), but never a changing count.

## B. Body layer

### P05 · Per-page maximum, and a minimum

**Assertion**: every page ≤ `limits.default`; index / inventory / troubleshooting pages may use `limits.index` etc., but **the exempt categories are listed in configuration**, never self-declared by a file. At the same time, a non-index page shorter than `min_doc_lines` is flagged.

**Why**: the cap forces the split "one session can hold this". The floor prevents gaming: without it, the cheapest way to pass the cap is to shred a coherent topic into fragments.

**Judgment (mechanical)**: per-file line counts against the configured limits and exemptions.

**Counter-example**: a 134-line page that calls itself an inventory; an index page at 200 lines; four 8-line pages that used to be one topic.

### P06 · Contents, tables, section size

**Assertion**: every page has a `## Contents` anchor list (≥3 entries) near the top; a section stays within `section_max_lines`; prefer tables to prose.

**Why**: an agent reads by "jump and extract". Anchors give the jump a landing point; tables bound the extraction.

**Judgment (mechanical)**: contents block present with ≥3 `#anchor` links; longest section under the cap (a WARN if not).

**Counter-example**: 120 lines containing four 60-line walls; a contents block whose anchors all miss.

### P07 · No dangling links or anchors

**Assertion**: every relative link resolves to a real file; every `#anchor` resolves to a real heading. Paths written in inline code (`` `docs/x.md` ``) should also exist, or be explicitly marked as relative to another root.

**Why**: this is the one honesty metric a machine can hold for you. One broken link takes the reader's trust in everything with it.

**Judgment (mechanical)**: parse `](path#anchor)`, resolve relative to the file; compare anchors to GitHub-style slugs; unresolved inline paths are a WARN (they may be relative to another root).

**Counter-example (measured)**: five places cite a manual as "existing" that was deleted long ago; a build script's error message points at a nonexistent README.

### P08 · Fixed confidence vocabulary

**Assertion**: the whole project uses one fixed set of markers (recommended `[verified]` / `[inferred]` / `[unverified]`), defined in exactly one place; upgrading a marker requires new evidence; no synonyms.

**Why**: without levels the reader cannot tell "read from code" from "actually ran". With levels but no fixed vocabulary, a `[confirmed]` variant means there is no vocabulary at all.

**Judgment (semi-mechanical)**: the script flags unknown variants (FAIL); lists pages with zero markers for human review.

**Non-code equivalent**: `[primary source checked]` / `[inferred from interviews]` / `[awaiting third-party confirmation]` — a different vocabulary is fine, as long as there is exactly one.

### P09 · Living documents carry no history

**Assertion**: a disproven or outdated statement is **deleted or rewritten in place**; it does not stay as a "previous version" section. History goes to the decision ledger (choices) and `_archive/` (whole pages). Living documents never route to the archive.

**Why**: with old and new statements side by side, which one the agent picks is random — and it is **silently** wrong.

**Judgment (mechanical)**: links from live pages to the archive are a WARN; an archive link in the entry's routing table is a FAIL; "previous version / used to / once" plus a concrete number is a WARN.

## C. Single source of truth

### P10 · One authority per fact

**Assertion**: any fact that will be cited (topology, prohibition, status, mechanism, conclusion) is written in exactly one place; everywhere else only links. Copying sentences is the only source of drift.

**Judgment (semi-mechanical)**: 3-gram similarity (threshold configurable, default 0.6) lists cross-file near-duplicate sentences; a human confirms whether they are the same fact.

**Counter-example**: the prohibition list written in full in both the entry and a sub-domain file; the mechanism explained both in a status page and in the decision ledger.

### P11 · A "single source" claim must have no copies

**Assertion**: if some place declares "X is the single authority / the only entry / single source of truth", the rest of the project must not contain a second copy of that content. **The declaration alone is not a single source.**

**Judgment (semi-mechanical)**: the script finds the declaration, then counts the same class of volatile assertions outside it; more than zero is a WARN.

**Counter-example (measured)**: "repo status is only authoritative in §8" was written, while four other places still described status — all stale.

## D. Decisions and state

### P12 · Decision ledger: four fields and a closed status set

**Assertion**: one row per decision where alternatives existed, with four columns: **decision / status / reason / evidence**. Status is one of `adopted | rejected | failed | pending`. `rejected` rows must state why the alternative was not used, with evidence.

**Why**: the most expensive waste is not doing the wrong thing; it is re-inventing something already rejected.

**Judgment (mechanical)**: the ledger exists; the header has the four columns; status values are within the closed set; `rejected` rows have reason and evidence.

**Non-code examples**: a research project records "method / vendor rejected"; a writing project records "narrative structure rejected".

### P13 · Open items are consumable

**Assertion**: all todos, blockers, and leftovers live in **one** structured table (or `STATE.opens[]`), with fixed fields: `id / item / status / next_action / evidence`. Status can move to `done`, and **a done row stays** (do not delete it).

**Why**: debt itself expires. A leftover saying "the docs still describe the old behavior" becomes false information once the docs are fixed — measured: 2 of 6 such leftovers had already been resolved while the ledger still claimed otherwise.

**Judgment (semi-mechanical)**: structure exists; fields complete; status within `open | blocked | done | dropped`; a human samples three rows.

### P14 · Exactly one machine-readable state pointer

**Assertion**: exactly one state file (JSON/YAML) with fixed keys: `schema_version, updated_at, last_session, phase, opens[], next_action`; each `opens[]` item has `id, status, next_action, evidence`.

**Why**: prose tables cannot be consumed by scripts, and cannot be merged safely across parallel sessions (last writer wins). A machine-readable pointer is the precondition for "back in 30 seconds".

**Key framing**: the state file is a **projection**, not the source of truth. The source of truth is `_sessions/` plus `decisions.md`; the state file can be rebuilt at any time. This is what makes write conflicts and crash recovery tractable (see P15).

### P15 · Only re-derive commands; reconcile on open

**Assertion**: every changing value in the state file carries `derived_at` and the `commands` that produced it (a shell command, or a procedure such as "export Y from system X and check column Z"). Documents never carry the value itself.

**Judgment (mechanical)**: `derived_at` and `commands` present; older than `stale_days` is a WARN.

**Reconciliation (mechanical)**: `updated_at` / `last_session` must not lag the newest session log. **Compare at open**: if the newest session is not the one named in `last_session`, the previous close did not finish (crash or timeout) — rebuild the state from logs before doing any work. This turns "dirty state after a crash" from unrecoverable into one recomputation.

**Counter-example**: a state file with `head: "a1b2c3d"` and no timestamp; a page saying "3 replies outstanding right now".

### P16 · Append-only session logs

**Assertion**: one file per session (`YYYY-MM-DD_<sid>.md`, ≤ the session limit: goal / what was done / files touched / what ran / where it is stuck / next command), `INDEX.md` is append-only; never let two sessions write the same file.

**Why**: the decision ledger records "why"; the session log records "where we are". Without it, coming back after a week means re-reading everything; with concurrent sessions, a shared file guarantees lost updates.

**Judgment (mechanical)**: the session directory exists; names match the date pattern; each file within the limit; `INDEX.md` exists.

## E. Execution layer

### P17 · Write-back names file, section, and trigger

**Assertion**: the entry has a "write-back obligations" section where each item names a **file plus section**, and each is attached to a trigger (closing checklist, script, hook, scheduled job). "Remember to update the docs" is not a trigger.

**Judgment (semi-mechanical)**: the section exists; at least one item references `path#section`; the workspace has a trigger (script / CI / hook / scheduler).

**Counter-example**: "update the docs when done" with no target; a target with nothing that checks it.

### P18 · A check entry point in the workspace

**Assertion**: one command runs the mechanical principles (links, anchors, line counts, volatile facts, state file, session logs). It can be `python tools/audit.py .`, a `make check` target, a pre-commit hook, or a scheduled job — but it must live in the workspace, not in someone's memory.

**Why**: this is the only investment that stops long-term rot. Well-structured knowledge layers die of "maintenance costs more than it returns"; automation pushes the marginal cost near zero.

**Judgment (mechanical)**: `tools/audit*`, `scripts/check*`, a make target, CI config, or a hook exists.

### P19 · Irreversible operations, with failure modes

**Assertion**: the entry lists operations that are **specific to this project** (not general advice), each with the failure mode or evidence: deleting a data directory, publishing externally, editing a shared sheet, overwriting originals.

**Judgment (semi-mechanical)**: a "never / irreversible" section with ≥3 items, each containing a concrete command, path, or system name; a human confirms they are not generic.

## F. Boundaries and budget

### P20 · Conclusion wording discipline

**Assertion**: when the environment cannot verify something (no compiler, no data, no credentials, cannot reach a person), never conclude "passes / works / fixed / confirmed". Give `[unverified]` plus a verification checklist (steps / method / criterion / what to do if it fails).

**Judgment (manual)**: check that a capability-boundary section exists; sample three conclusions for markers; check the checklist has a criterion column.

**Counter-example**: "build passes" written on a machine that cannot build; an `[unverified]` item quoted downstream as a conclusion.

### P21 · Cold-start budget, single routing table

**Assertion**: entry + state file + top index ≤ `budget_tokens`; and **exactly one routing table** — the index page describes what each page covers, it does not repeat "I want… → read which".

**Why**: cold-start cost decides whether a new session is worth starting. Two routing tables are a high-risk instance of P10, because both evolve.

**Judgment (mechanical)**: estimate tokens (CJK ≈ 1 token per character, ASCII ≈ 4 bytes per token); ≥2 routing tables is a FAIL.

### P22 · Evidence resolves

**Assertion**: every `file:line` citation (`` `path:123` ``, `` `path:123-130` ``) points to a **real file**, and the line is within that file's length.

**Why**: this is the only mechanical defense against invented citations. Links break and anchors drift, but "`:42` points into a 4-line file" is hard evidence. In one real project it caught five citations to deleted files on the first run.

**Judgment (mechanical)**: resolve in order — file directory, ancestor directories, workspace root, same-name suffix index; a line out of range, or a missing file under a docs path, is a FAIL; a same-name file from another version is a WARN.

**Exception**: evidence pointing outside the workspace (EDA logs, external exports) can only be a WARN; those must state where they can be retrieved.

**Counter-example**: `` `spec.md:42` `` when the file has 4 lines; `` `vcs_simv.log:43563` `` after the log was overwritten by the next run.

## Order of judging

1. `python scripts/audit.py <workspace>` → fix every FAIL first.
2. Work through the printed manual list for P03 / P08 / P10 / P11 / P12 / P13 / P17 / P19 / P20.
3. Only fix the area this session touched. The purpose is to lower maintenance cost, not to trigger a rewrite.

## Dependencies

- P04 / P10 / P11 / P15: volatile things get copied.
- P02 / P21: duplicate routing.
- P13 / P16: no append-only layer.
- P14 / P15 / P16 / P22: event source → projection → citation.
- P18 keeps all the others from rotting.
