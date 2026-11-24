# 02 · sources and evidence cards

## Contents

- [1. Source list](#1-source-list)
- [2. Evidence cards](#2-evidence-cards)
- [3. Missing sources](#3-missing-sources)

## 1. Source list

| # | Source | Type | Reachability | Confidence |
| --- | --- | --- | --- | --- |
| A | Internal specification | primary | readable here | high |
| B | Export provided by the business owner | primary | summary only | medium |
| C | Public technical report | secondary | readable here | medium |

## 2. Evidence cards

### Source A

- Fact: the specification fixes the boundary value and gives a counter-example. `[verified]` at `_sources/A/spec.md:3`
- Relevance: it decides how "irreversible" is judged.

### Source B

- Fact: the export has only the summary column; the detail column is absent. `[verified]` at `_sources/B/summary.csv:1`
- Impact: we cannot recompute it; only the provided total can be quoted `[inferred]`.

### Source C

- Fact: the public report's interval agrees with source A's value. `[inferred]` (definitions may differ; needs a manual comparison)

## 3. Missing sources

| Source | Missing | Impact | Open item |
| --- | --- | --- | --- |
| B | detail export | the conclusion can only be an interval, not a point | O-001 |
