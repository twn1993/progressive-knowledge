# Bootstrap in 30 minutes

> Goal: after this page, a new project passes the mechanical checks.
> **This is all you need to read to set up**; no-git fallbacks, migration detail, scale tiers, and failure modes are in `bootstrap-full.md`.
> No assumptions about git, code, or builds. **Writing rules are in `writing.md`**; this page is only skeleton and process.

## 0. Pick a tier + answer three questions

| Scale | Tier | Files to create |
| --- | --- | --- |
| One-off, solo, < 1 week | **L0** | 4 (entry / STATE / decisions / `_sessions/`) |
| Solo, sustained weeks | **L1 (recommended)** | 4 + `docs/00_INDEX.md` + `tools/` |
| Team / branches / months | **L2** | L1 + topic tree + `_archive/` + separate decision file |

Answer each in one sentence, with no "probably / should":

1. **What is the deliverable?** (a running system / a report / verified data / a document set) → goes into the entry.
2. **Which step is irreversible?** (delete data / publish / overwrite originals / spend money / submit to an external system) → goes into the entry's "never" section.
3. **What can this machine not verify?** (no permission / no data / no environment) → goes into the entry's capability boundary.

## 1. Skeleton

```
<workspace>/
├── AGENTS.md | WORKSPACE.md    # the only entry (≤ limits.default)
├── docs/
│   ├── 00_INDEX.md       # L1+: what each page covers (no routing)
│   ├── STATE.json        # state (a projection, not the truth)
│   ├── decisions.md      # decision ledger
│   ├── _sessions/        # one file per session + INDEX.md
│   ├── _archive/         # L2: whole-page archive, never an entry
│   └── <topic>/          # L2: 00_INDEX + body pages
└── tools/
    ├── check.py          # copy from the kit
    └── audit.config.json # set entry_files / docs_root / tier
```

**Do not copy the whole kit into the workspace**: copy the skeletons and `tools/`; if the kit lives inside, add it to `skip_dirs` (`_kit` is excluded by default).

## 2. Write the entry (order is the principle)

| Step | What to write | Principle |
| --- | --- | --- |
| 1 | One sentence: what this is, the deliverable, "this page is the only entry" | P01 |
| 2 | Capability boundary: what works here / what cannot be verified | P20 |
| 3 | Irreversible operations specific to this project, with consequences | P19 |
| 4 | Structure: the blocks, their sources/owners, read-only or not (**structural facts only**) | P04 |
| 5 | "State authority" pointing at `STATE.json` + one re-derive command | P11/P15 |
| 6 | Intent routing table (≥5 rows) | P02 |
| 7 | Conventions: size limits, marker vocabulary, single authority (**reference config keys, do not copy numbers**) | P05/P08/P10 |
| 8 | Write-back obligations: each `path#section` + a trigger | P17 |
| 9 | Archive rules: where old pages go, who may not link to them | P09 |

Template: `templates/AGENTS.md.tmpl`.

## 3. State file (the only state a session reads)

```json
{
  "schema_version": 1,
  "updated_at": "2026-01-01T10:00:00+08:00",
  "last_session": "2026-01-01_<sid>",
  "phase": "phase name",
  "derived_at": "2026-01-01T09:50:00+08:00",
  "commands": {"open items": "<re-derive command or procedure>"},
  "opens": [{"id": "O-001", "item": "…", "status": "blocked",
              "next_action": "…", "evidence": "<path:line>"}],
  "next_action": "the single thing this session should do"
}
```

Three hard rules:

- **STATE is a projection**: the truth is `_sessions/` + `decisions.md`; it can be rebuilt.
- `status` ∈ `open|blocked|done|dropped`; `done` rows stay.
- **Do not store history in STATE**: it answers "where are we, what next", within one screen.

Template: `templates/STATE.json.tmpl`.

## 4. Session protocol

**Open (≤2 minutes)**

```
1. Read the entry
2. Read STATE.json
3. Read the last 3 lines of _sessions/INDEX.md
4. Follow next_action or the routing table; open exactly one document
5. Reconcile: STATE.last_session ≠ newest session file ⇒ rebuild STATE first
6. derived_at too old ⇒ run commands first
```

**Close (≤5 minutes, not optional)**

```
1. Run the check command (no new FAIL)
2. Write _sessions/<date>_<sid>.md (≤ limit) and append one line to INDEX
3. Update STATE: opens / next_action / updated_at / last_session
4. New approach, rejected approach, failed route → one decision row
5. Changing values → update commands and derived_at only
```

## 5. Acceptance

```bash
python tools/check.py .            # or: python tools/audit.py . --tier L1
```

| Gate | Criterion |
| --- | --- |
| Hard | the tier's principles are PASS: P01/P04/P14/P15/P16/P18, plus P07/P22 at L1 |
| Soft | no more than 3 WARN of the same kind, and none new |
| Manual | P03/P08/P10/P11/P12/P13/P17/P19/P20 have explicit answers |
| Self-consistent | hand the entry to a stranger; they can take over within 30 minutes |

**Run it again in 14 days.** If WARN grows, maintenance cost did not drop — fix P18 (the trigger) before fixing documents.

---

For no-git fallbacks, migration from an existing project, scale tiers, and common failure modes, see `bootstrap-full.md`.
