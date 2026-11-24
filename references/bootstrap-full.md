# Bootstrap reference (read on demand)

> **The normal path is `bootstrap.md` (30 minutes; that is all you need to set up).**
> This page keeps: no-git fallbacks, migration from an existing project, scale tiers, common failure modes, and the reasoning behind the write order.

## 1. No git? Three substitutions

| Need | With git | Without git |
| --- | --- | --- |
| What changed last time | `git log` | `_sessions/` logs + one `done` row per unit |
| What version this is | commit hash | version number / date stamp / `MANIFEST.md` (path, size, mtime, source) |
| Rollback | `checkout` | `_snapshots/YYYY-MM-DD/` copies, or a read-only export |
| Parallel safety | branches | one file per session + append-only index (P16) |

No principle changes. P04 forbids hard-coded volatile values regardless of origin; P15 asks for a command **or a procedure** ("open system X, export Y, check column Z").

## 2. Git or not?

| Situation | Recommendation | Alternative |
| --- | --- | --- |
| Text-heavy, multiple people, rollback matters | use git, but **as change history only** | — |
| Solo docs / research | optional | session logs + snapshot directory |
| Binary data, shared drive | git may not fit | version numbers + `MANIFEST.md` |
| Shared drive, concurrent edits | git will not save you | one file per session + append-only index |

## 3. Migrating an existing project (three steps, never one rewrite)

| Step | Action | Output | Risk control |
| --- | --- | --- | --- |
| 1 | Create only the entry, STATE, decisions, and the check script; **do not touch existing docs** | a workspace that runs the checker | existing content stays readable; zero breakage |
| 2 | Split existing long docs by intent, one page at a time; run the checker after each | topic tree | one page per change; fix links as you go |
| 3 | Delete duplicate copies (P10/P11) and archive old pages (P09) | single source of truth | confirm something links to a page before deleting it |

**Iron rule during migration**: every change may **remove** volatile state, never add it.

## 4. Scale tiers

| Scale | Files | When to upgrade |
| --- | --- | --- |
| One-off (< 1 week) | entry + `_sessions/` | when a second parallel session appears, add STATE |
| Solo, sustained (weeks) | the L0 four | when topics reach 3, add `docs/` tree |
| Team / multi-week / multi-source | standard structure + separate decision file | when rules fork, add a child entry |
| Long-lived (> 3 months) | standard + archive + scheduled check | when reused across projects, extract a template |

## 5. Writing order and why

1. **Entry first.** It is the only file injected every session; nothing else matters if it is wrong.
2. **State second.** Without it, the second session cannot answer "where are we".
3. **Session index third.** It is the only place that answers "what happened last time".
4. **Decisions fourth.** It prevents re-inventing rejected approaches.
5. **Top index fifth.** It explains what each page covers; routing stays in the entry.
6. **Body pages last, one topic at a time.** They are the expensive part and the least urgent.

## 6. Common failure modes (all observed)

| Symptom | Root cause | Fix |
| --- | --- | --- |
| Six stale status claims within a week | status written into the entry or index (P04) | move to `STATE.json` with commands |
| The "single authority" claim is ineffective | copies were never deleted (P11) | delete copies, leave links |
| The debt ledger itself goes stale | no `done` status (P13) | add the status column; keep the row |
| Parallel sessions overwrite each other | one shared progress file (P16) | one file per session + append-only index |
| Docs become scary to edit | no checker (P18) | write a 30-line script that only checks links and sizes |
| Newcomers still read the wrong page | two routing tables (P21) | keep one in the entry; the index describes pages |
| No git, so governance is abandoned | git treated as a prerequisite | session logs + MANIFEST + snapshots |

## 7. Template index

| Template | Fills |
| --- | --- |
| `templates/AGENTS.md.tmpl` | entry: boundary, prohibitions, structure, routing, conventions, write-back |
| `templates/STATE.json.tmpl` | state pointer |
| `templates/decisions.md.tmpl` | decision ledger |
| `templates/session.md.tmpl` | one session log |
| `templates/session-INDEX.md.tmpl` | append-only session index |
| `templates/00_INDEX.md.tmpl` | top index or topic index |
| `templates/AGENTS.openspec.md.tmpl` | entry when OpenSpec is used |
| `templates/STATE.openspec.json.tmpl` | state pointer with `active_change` |

## 8. Why the closing protocol is not negotiable

The closing step is the only place where the system can become wrong **silently**. If the session ends without a log and a state update, the next session reads a state that claims to be current but is not. P15's reconciliation turns that into a warning; the protocol prevents it in the first place. Five minutes at the end buys the next session's first thirty seconds.
