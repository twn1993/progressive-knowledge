# 22 principles (quick reference)

> This is the only page you need when bootstrapping. Rationale, counter-examples, and exceptions live in
> `principles-full.md` — read it only when judging whether a principle applies, or when changing thresholds.
> **Thresholds are defined only in `audit.config.json`**; this page never repeats the numbers.

## Pick a tier first

| Tier | Principles | Use for | Cold start |
| --- | --- | --- | --- |
| **L0** | P01 P04 P14 P15 P16 P18 | one-off tasks, single person, < 1 week | ~1k tokens |
| **L1** | L0 + P02 P05 P07 P13 P17 P22 | sustained solo work (**default**) | ~1.5k tokens |
| **L2** | all 22 | teams, branches, months | ~2k tokens |

```bash
python tools/audit.py . --tier L1   # or set "tier" in audit.config.json
```

## If you remember only three

1. **Volatile values never live in the entry** (P04) — write how to fetch the value, not the value.
2. **One state file, and it is a projection** (P14/P15) — the truth is in session logs; state can be rebuilt.
3. **Evidence must resolve** (P22) — a `path:line` that does not point at a real line is not evidence.

## All principles

| ID | Principle | Mechanical criterion | Tier |
| --- | --- | --- | --- |
| P01 | One entry file with a size cap | root entry exists, lines ≤ `limits.default`, first 10 lines declare "only entry" | L0 |
| P02 | Intent routing, no linear reading | ≥`routing_min_rows` rows of "I want… → read which" plus an explicit "do not read in order" | L1 |
| P03 | Sub-domain files implement, never relax | child entry links to the parent; no "prefer / usually" where the parent says "never" | L2 |
| P04 | Zero volatile facts in the resident layer | no commit hashes, counts, `N items`, progress percentages | L0 |
| P05 | Per-page max and min | within `limits.*`; not below `min_doc_lines` (anti-fragmentation) | L1 |
| P06 | Headings, tables, section size | `## Contents` with ≥3 anchors before line 40; section ≤ `section_max_lines` | L2 |
| P07 | No dangling links or anchors | every relative link resolves; every `#anchor` matches a real heading | L1 |
| P08 | Fixed confidence vocabulary | only configured markers; no synonyms | L2 |
| P09 | Living docs carry no history | archive is not routed to; old values are gone | L2 |
| P10 | One authority per fact | cross-file similarity below `similarity_threshold` | L2 |
| P11 | "Single source" must have no copies | no volatile claims outside the declared authority | L2 |
| P12 | Decision ledger: four fields, closed status set | decision/status/reason/evidence present; status ⊆ `decision_statuses` | L2 |
| P13 | Open items are consumable | `opens[]` has id/status/next_action/evidence; closed set | L1 |
| P14 | Exactly one machine-readable state pointer | one state file, required keys, `opens[]` four keys | L0 |
| P15 | Only re-derive commands; reconcile on open | `derived_at`/`commands` present; `last_session` not behind the newest log | L0 |
| P16 | Append-only session logs | one file per session, ≤ limit, `INDEX.md` exists | L0 |
| P17 | Write-back names file + section + trigger | section exists, references `path#section`, a trigger exists | L1 |
| P18 | A check entry point in the workspace | script / make target / CI / hook | L0 |
| P19 | Irreversible-operations list | "never / irreversible" section, ≥3 items with a command or path | L2 |
| P20 | Conclusion wording discipline | capability boundary + verification checklist (semantics still manual) | L2 |
| P21 | Cold-start budget, single routing table | entry+state+top index ≤ `budget_tokens`; ≤1 routing table | L2 |
| P22 | Evidence resolves | `path:line` file exists and the line is within range | L1 |

## Three kinds of judging

| Kind | Meaning | Who |
| --- | --- | --- |
| Mechanical | script returns PASS/FAIL | `audit.py` |
| Semi-mechanical | script shows evidence, a human decides | printed "manual checks" |
| Manual | only a human can judge (P20 and friends) | you |

## Dependencies between principles

- P04 / P10 / P11 / P15: **volatile things get copied** — fix them together.
- P02 / P21: **duplicate routing**.
- P13 / P16: **no append-only layer**.
- P14 / P15 / P16 / P22: the **event source → projection → citation** chain.
- P18 is the only mechanism that keeps the other 21 from rotting.

## Order of judging

1. Pick a tier → `python tools/audit.py . --tier <tier>`.
2. Fix FAIL first (all are cheap), then read WARN.
3. Work through the printed manual list only for the area you touched this session — **do not rewrite every document for compliance**.
