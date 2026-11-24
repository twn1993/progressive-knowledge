#!/usr/bin/env python3
"""Minimal knowledge-layer checker: entry, sizes, contents, links, anchors,
path:line evidence, volatile values, state fields, session logs, duplicate
routing tables, duplicated long sentences. Read-only. No dependencies.

Usage: python check.py [workspace_root]
Exit:  0 = no FAIL, 1 = FAIL present.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
ENTRY = [ROOT / n for n in ("AGENTS.md", "WORKSPACE.md", "CLAUDE.md") if (ROOT / n).is_file()]
DOCS = ROOT / "docs"
LIMIT, INDEX_LIMIT, SESSION_LIMIT, MIN_LINES = 120, 135, 20, 10
MARKERS = ("[verified]", "[inferred]", "[unverified]")
fails, warns = [], []


def text(p):
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def rel(p):
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def slug(heading):
    s = heading.strip().lower().replace("`", "")
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"\s", "-", s).strip()


def docs():
    out = []
    if DOCS.is_dir():
        out += [p for p in DOCS.rglob("*.md") if "_archive" not in p.as_posix()]
    out += [p for p in ENTRY if p.is_file()]
    return sorted(set(out))


def routing_tables(t):
    """Count tables that look like 'intent -> document' routing."""
    n, lines = 0, t.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|") or i + 1 >= len(lines):
            continue
        if set(lines[i + 1].replace("|", "").strip()) - set("-: "):
            continue
        rows, j = [], i + 2
        while j < len(lines) and lines[j].startswith("|"):
            rows.append(lines[j])
            j += 1
        linky = sum(1 for r in rows if re.search(r"\]\(|`[^`]+\.md`", r))
        if len(rows) >= 3 and linky >= 3 and re.search(r"I want|want to|intent", line, re.I):
            n += 1
    return n


def main():
    if not ENTRY:
        fails.append("missing root AGENTS.md")
    for e in ENTRY:
        n = len(text(e).splitlines())
        if n > LIMIT:
            fails.append(f"{e.name}: {n} lines > {LIMIT}")

    all_docs = docs()
    for p in all_docs:
        t = text(p)
        lines = t.splitlines()
        n = len(lines)
        is_index = "INDEX" in p.name.upper() or p.name.startswith("00_")
        is_entry = p in ENTRY
        limit = INDEX_LIMIT if is_index else LIMIT
        if n > limit:
            fails.append(f"{rel(p)}: {n} lines > {limit}")
        head = lines[:40]
        has_contents = any(x.strip().startswith("##") and re.search(r"Contents|TOC", x) for x in head)
        if n >= 30 and not is_index and not is_entry and not has_contents:
            fails.append(f"{rel(p)}: missing a '## Contents' block")
        if 0 < n < MIN_LINES and not is_index and not is_entry and "_sessions" not in p.as_posix():
            warns.append(f"{rel(p)}: only {n} lines (check it is not a fragment)")

        for m in re.finditer(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", t):
            raw = m.group(1)
            if raw.startswith(("http", "mailto:", "#")):
                continue
            path, _, anchor = raw.partition("#")
            target = (p.parent / path).resolve() if path else p
            if path and not target.exists():
                fails.append(f"{rel(p)}: broken link {raw}")
            elif anchor and target.suffix.lower() == ".md" and target.is_file():
                heads = {slug(re.sub(r"^#+\s*", "", l)) for l in text(target).splitlines() if l.startswith("#")}
                if anchor not in heads:
                    fails.append(f"{rel(p)}: missing anchor {raw}")

        for m in re.finditer(r"`([^`\s]+\.\w+):(\d+)(?:-(\d+))?`", t):
            tgt = (p.parent / m.group(1)).resolve()
            if not tgt.exists():
                tgt = (ROOT / m.group(1)).resolve()
            if not tgt.exists():
                warns.append(f"{rel(p)}: evidence outside the workspace ({m.group(1)})")
                continue
            total = len(text(tgt).splitlines())
            if int(m.group(3) or m.group(2)) > total:
                fails.append(f"{rel(p)}: evidence line out of range {m.group(0)} ({total} lines)")

    volatile = [
        r"\bHEAD\b[^\n|]{0,24}\b[0-9a-f]{7,40}\b",
        r"(?:commit)[^\n|]{0,16}\b[0-9a-f]{7,40}\b",
        r"[×]\s*\d+",
        r"\d+\s*(?:uncommitted|untracked|changed|items?|commits?)",
        r"status --porcelain[^\n]{0,40}\d+",
        r"(?:current|currently|latest|as of)[^\n]{0,12}\d+\s*(?:items?|files?|commits?)",
        r"\d{1,3}\s*%\s*(?:done|complete|finished)",
    ]
    targets = list(ENTRY)
    state_path = DOCS / "STATE.json"
    if state_path.is_file():
        targets.append(state_path)
    for p in targets:
        for i, line in enumerate(text(p).splitlines(), 1):
            for rx in volatile:
                m = re.search(rx, line, re.I)
                if m:
                    fails.append(f"{rel(p)}:{i}: volatile value '{m.group(0)}'")

    if not state_path.is_file():
        fails.append("missing docs/STATE.json")
    else:
        try:
            st = json.loads(text(state_path))
            for k in ("schema_version", "updated_at", "last_session", "phase",
                      "derived_at", "commands", "opens", "next_action"):
                if k not in st:
                    fails.append(f"STATE.json: missing field {k}")
        except json.JSONDecodeError:
            fails.append("STATE.json: not valid JSON")

    sd = DOCS / "_sessions"
    if not sd.is_dir():
        fails.append("missing docs/_sessions/")
    else:
        logs = [p for p in sd.glob("*.md") if p.name.lower() != "index.md"]
        for p in logs:
            n = len(text(p).splitlines())
            if n > SESSION_LIMIT:
                fails.append(f"{rel(p)}: {n} lines > {SESSION_LIMIT}")
        if not (sd / "INDEX.md").is_file():
            fails.append("missing docs/_sessions/INDEX.md")

    idx = DOCS / "00_INDEX.md"
    if ENTRY and routing_tables(text(ENTRY[0])) and idx.is_file() and routing_tables(text(idx)):
        warns.append("routing table appears in both the entry and docs/00_INDEX.md (keep one)")

    seen = {}
    for p in all_docs:
        if "_sessions" in p.as_posix():
            continue
        for line in text(p).splitlines():
            s = line.strip()
            if len(s) < 40 or s.startswith(("|", "#", "```", "- [", ">")):
                continue
            seen.setdefault(re.sub(r"\s+", "", s), set()).add(rel(p))
    dup = [k for k, v in seen.items() if len(v) > 1]
    if dup:
        warns.append(f"{len(dup)} long sentence(s) appear in multiple files: {dup[0][:40]}…")

    for f in fails:
        print("FAIL " + f)
    for w in warns:
        print("WARN " + w)
    print(f"\nFAIL {len(fails)} · WARN {len(warns)} · files {len(all_docs)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
