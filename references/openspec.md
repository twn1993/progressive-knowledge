# Composing with OpenSpec

> Goal: **one generic `AGENTS.md`** that connects OpenSpec's "changes and specs" with this kit's "project state, session memory, evidence" — without duplicating definitions or overwriting each other.
> Templates: `templates/AGENTS.openspec.md.tmpl` + `templates/STATE.openspec.json.tmpl`.

## 1. Who owns what (do not cross)

| Layer | Owner | Content | Authority |
| --- | --- | --- | --- |
| Changes and specs | **OpenSpec** | `openspec/changes/<name>/{proposal,specs,design,tasks}.md`; `openspec/specs/**` is "the system as built" | OpenSpec CLI / skills |
| Entry and boundaries | this kit's `AGENTS.md` | single entry, intent routing, capability boundary, irreversible operations, write-back | that file |
| Project state | `docs/STATE.json` | `phase / active_change / opens[] / next_action / last_session` | that file (**a projection**) |
| Process memory | `docs/_sessions/` | one file per session, append-only | session logs |
| Choices and rejections | `docs/decisions.md` | decision / status / reason / evidence | that file |
| Reference knowledge | `docs/<topic>/` | mechanisms, how to run, pitfalls, boundaries | each page |

**Hard rules**: `AGENTS.md` does not restate OpenSpec usage (its skill docs are the source); `STATE.json` does not store task lists (`tasks.md` does); `specs/` does not store investigation notes (that is `docs/` and session logs).

## 2. Three things OpenSpec does not cover, and the fix

| Gap | Consequence | Fix |
| --- | --- | --- |
| **Evidence field** | measured values go into `design.md` prose; `validate` ignores them | write `path:line`; `audit.py` P22 verifies it resolves |
| **Project-level state** | only a single change's `completedTasks/totalTasks`; no "what next" | `STATE.active_change` + `next_action`; `openspec status --json` only feeds `change_state` |
| **Reference knowledge** | no home for "how to run / what is missing / what bites" | `docs/<topic>/`, constrained by P05/P07 |

## 3. Initialization order (10 minutes, once)

```bash
# 1) this kit's skeleton (do not copy the whole kit)
cp <kit>/scripts/check.py <ws>/tools/
cp <kit>/scripts/audit.py <ws>/tools/ && cp <kit>/scripts/audit.config.json <ws>/tools/
cp <kit>/templates/AGENTS.openspec.md.tmpl <ws>/AGENTS.md    # fill <PROJECT> and §1/§2
cp <kit>/templates/STATE.openspec.json.tmpl <ws>/docs/STATE.json
mkdir -p <ws>/docs/_sessions <ws>/docs/<topic>

# 2) OpenSpec (2.x installs skills machine-wide; add --scope project so teammates and CI get them)
openspec init --scope project

# 3) First point: a change that only verifies, without changing behavior
openspec new verify-<point>
#   set skip_specs: true in .openspec.yaml and explain in proposal.md why it is not a behavior change
openspec status --change verify-<point> --json
openspec validate --all

# 4) Close
python tools/check.py .
```

> OpenSpec 2.x `init` cleans up legacy marker blocks in `CLAUDE.md` / `AGENTS.md` (with confirmation).
> If you wrote them under 1.x, let `init` remove them before dropping this template in — do not keep two instruction blocks.

## 4. "Should this point be a change?"

| Test | Decision |
| --- | --- |
| After completion, someone can observe different behavior | create a change (with a delta or an explicit `skip_specs`) |
| Only "what we know" changes (ran once, measured once, read code) | no change; session log + one `STATE.opens` row |
| Refactor with unchanged behavior | create a change, justify in `design.md`; do not hide behind `skip_specs` |

## 5. Three checks worth automating

1. **State consistency**: when `STATE.active_change` is set, `openspec/changes/<name>/` must exist; all tasks checked but `active_change` still set → WARN (time to archive).
2. **Archive closure**: every change name under `openspec/changes/archive/**` must appear once in `docs/_sessions/` (archiving without a trace breaks the memory chain).
3. **Spec evidence**: add `openspec/specs` to `docs_root` in `audit.config.json` (P07/P22 then apply; if specs are naturally long, list them in `exempt_files`).

## 6. When not to use OpenSpec

- Work dominated by debugging and measurement that changes no behavior (many zero-delta changes turn `changes/` into a junk drawer).
- Non-code tasks (research, writing, operations): there is no capability to write; use `docs/` + `STATE`.
- Very frequent small edits (ten a day): the folder ceremony costs more than it returns; use session logs.

## 7. Verified

A temporary workspace was built in this order (with a minimal `openspec/changes/add-alpha/` and `openspec/specs/`):

```
L1  FAIL 0 · WARN 0 · PASS 12
L2  FAIL 0 · WARN 0 · PASS 22
```

`AGENTS.md` was 81 lines; `STATE.json` passed P14/P15 (including `active_change` and `last_session` reconciliation); every `path:line` evidence resolved.
