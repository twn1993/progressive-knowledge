# Progressive Knowledge

**A file-based knowledge layer that lets an agent pick a long-running project back up in ~1.5k tokens.**

Most agent setups die the same way: every session starts empty, the history lives in the conversation, and the moment you switch sessions the context is gone. Piling everything into one context window does not work either — effective context is far smaller than the advertised size, and LLM summaries drop details.

This repo is a small, auditable structure that fixes that:

- **one entry file** (`AGENTS.md`) — routing and hard constraints, never status;
- **one state pointer** (`docs/STATE.json`) — a *projection* that can be rebuilt from logs;
- **append-only session logs** and a **decision ledger** — what happened, and what was rejected;
- **mechanical checks** (`scripts/check.py`, `scripts/audit.py`) — so the structure cannot silently rot.

It assumes **no git, no build, no code**. It works for software repos, verification environments, research projects, long-form writing, and operations runbooks.

## Why it is shaped this way

| Problem | Measured / observed | Design answer |
|---|---|---|
| Effective context ≪ advertised | 128K models degrade well before 128K; non-literal recall drops much earlier | load a small entry, fetch one document at a time |
| LLM summaries lose detail | controlled tests retain ≤16% of recurring details | keep original text + `path:line`, summarize only as an index |
| Status written into docs goes stale | a project's entry had 6 stale status claims within 7 days | status lives in one JSON file with re-derive commands |
| Duplicated facts diverge | the same rule copied into 3 places, all different | one authority per fact; everything else links |
| "Remember to update the docs" | nobody remembers | mechanical checks + a closing checklist |

## Quick start

```bash
# install as a pi skill (user-level)
cp -r progressive-knowledge ~/.pi/agent/skills/

# or bootstrap a workspace by hand
mkdir -p <ws>/docs/_sessions <ws>/tools
cp scripts/check.py <ws>/tools/
cp templates/AGENTS.md.tmpl <ws>/AGENTS.md      # fill the placeholders
cp templates/STATE.json.tmpl <ws>/docs/STATE.json
python <ws>/tools/check.py <ws>                 # must be FAIL 0
```

With pi, the entry file is injected automatically; a new session then reads the entry, the state pointer, the last lines of the session index, and exactly one document.

## What is in here

| Path | What it is |
|---|---|
| `SKILL.md` | pi skill entry (loaded on demand) |
| `references/principles.md` | 22 principles, one-line criteria, tiers |
| `references/principles-full.md` | the long form: rationale, counter-examples, exceptions |
| `references/bootstrap.md` | 30-minute setup |
| `references/bootstrap-full.md` | reference: no-git fallbacks, migration, scale tiers, failure modes |
| `references/writing.md` | what to write, how to write it incrementally, what to verify |
| `references/seed.md` | a single copy-paste file that makes a model build the layer |
| `references/openspec.md` | optional: how this composes with OpenSpec |
| `templates/` | ready-to-copy skeletons (entry, index, state, decisions, session) |
| `scripts/check.py` | zero-dependency checker: links, anchors, line counts, evidence, state |
| `scripts/audit.py` | fuller checker: 22 principles, tiers, config |
| `example/` | a complete sample workspace that passes every check |

## The three roles (this is the whole trick)

| Role | When | Reads | Cost |
|---|---|---|---|
| **Builder** | day one, once | `references/principles.md` + `references/bootstrap.md` + templates | ~3.5k tokens |
| **Runner** | every session | entry + `STATE.json` + last 3 index lines + **one** document | ~1.5k tokens, capped |
| **Auditor** | at close | nothing — it scans bytes, never enters the model context | ~0.7k output |

`references/principles-full.md` is read only when judging whether a principle applies or when changing the rules. `scripts/audit.py` is executed, never read.

## Tiers

| Tier | Principles | Use for |
|---|---|---|
| **L0** | 6 | one-off tasks, single person, under a week |
| **L1** | 12 | sustained solo work (recommended default) |
| **L2** | 22 | multiple people, several branches, months |

```bash
python scripts/audit.py <ws> --tier L1
```

## Verified

| Target | Result |
|---|---|
| `example/` | L0 6/6, L1 12/12, L2 22/22 — 0 FAIL, 0 WARN |
| Negative control (inject `HEAD a1b2c3d` + broken links) | fails as expected |
| A real long-running project | 6 FAIL at L1: stale status claims, one oversized page, no state/session/check layer |

## Honest limits

1. There is **no controlled experiment** showing that files beat vector stores; what is supported is "retrieval beats stuffing" and "summaries lose detail".
2. `P10` / `P11` / `P13` are heuristics — 3-gram similarity misses paraphrased duplicates and flags template repetition.
3. Line limits are a proxy, not proof that a session fits.
4. The whole thing depends on someone writing 20 lines at the end of a session. Without `P18` (a check entry point), everything else rots within weeks.

## License

MIT.
