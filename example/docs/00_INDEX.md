# Demo project · documentation index

> One sentence: this set covers the question, the evidence, and the draft conclusion.
> Routing lives in the root `WORKSPACE.md §4`; this page only says what each page covers.

## Contents

- [1. Document map](#1-document-map)
- [2. Conventions](#2-conventions)
- [3. Known boundaries](#3-known-boundaries)
- [4. State](#4-state)

## 1. Document map

| Tree | Covers | Does not cover | Entry |
| --- | --- | --- | --- |
| `topic/` | question, evidence, draft | environment setup, history | [00_INDEX](topic/00_INDEX.md) |

## 2. Conventions

| Marker | Meaning | Allowed action |
| --- | --- | --- |
| `[verified]` | has a source location, reproducible here | may only be downgraded, never invented |
| `[inferred]` | follows from material, not executed | may be upgraded with new evidence |
| `[unverified]` | must be confirmed by the outside party | only their confirmation removes it |

- Relative links; a section ≤25 lines; tables over prose.
- Never silently upgrade a marker; never write changing values on this page.

## 3. Known boundaries

1. Some sources live on an internal network this machine cannot reach.
2. One class of conclusions requires the business owner's confirmation.
3. Open blockers are listed in [`STATE.json`](STATE.json).

## 4. State

State is not on this page: see [`STATE.json`](STATE.json) (the only authority). To get a value, run its `commands`.
