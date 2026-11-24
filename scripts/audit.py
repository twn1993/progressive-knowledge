#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit.py - progressive knowledge-layer auditor (read-only, no dependencies)

Usage:
    python audit.py <workspace_root>                 # full audit
    python audit.py <workspace_root> --only P04,P07  # selected principles
    python audit.py <workspace_root> --json          # machine-readable output
    python audit.py <workspace_root> --config path   # explicit config

Exit codes: 0 = no FAIL; 1 = FAIL present; 2 = config or path error.

Config precedence: --config > <script_dir>/audit.config.json > <root>/tools/audit.config.json > built-in defaults.
The script is read-only; it writes nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- defaults

DEFAULTS = {
    "_doc": "Paths and thresholds are configurable; copy this file to <workspace>/tools/audit.config.json",
    "_doc2": "No assumptions about git, code, or builds; entry_files and docs_root accept several candidates, first existing wins",
    "entry_files": ["AGENTS.md", "WORKSPACE.md", "CLAUDE.md", "BRIEF.md"],
    "docs_root": ["docs", "notes"],
    "state_file": "docs/STATE.json",
    "session_dir": "docs/_sessions",
    "decisions_file": "docs/decisions.md",
    "opens_file": "docs/opens.md",
    "archive_dirs": ["docs/_archive", "docs/archive"],
    "skip_dirs": [".git", "node_modules", ".venv", "venv", "__pycache__",
                  ".pi-subagents", ".pytest_cache", "dist", "build", "out", "_kit", "kit"],
    "limits": {"default": 120, "index": 135, "inventory": 135, "pitfalls": 135},
    "exempt_files": [],
    "exempt_categories": ["index", "inventory", "pitfalls"],
    "markers": {"verified": "[verified]", "inferred": "[inferred]", "unverified": "[unverified]"},
    "forbidden_marker_variants": ["[confirmed]", "[validated]", "[pending]", "[unconfirmed]", "[tested]", "[ran]"],
    "routing_min_rows": 5,
    "section_max_lines": 25,
    "similarity_threshold": 0.6,
    "dup_max_reports": 10,
    "budget_tokens": 8000,
    "stale_days": 14,
    "check_inline_paths": True,
    "inline_path_max_reports": 12,
    "volatile_scope": ["entry", "index"],
    "tier": "L2",
    "min_doc_lines": 15,
    "state_lag_hours": 24,
    "alt_roots": [],
    "evidence_max_reports": 15,
    "suffix_index_cap": 300000,
}

# ---------------------------------------------------------------- principle metadata

PRINCIPLES = {
    "P01": ("Single entry with a size cap", "mechanical"),
    "P02": ("Intent routing, no linear reading", "mechanical"),
    "P03": ("Sub-domain files implement, never relax", "semi"),
    "P04": ("Zero volatile facts in the resident layer", "mechanical"),
    "P05": ("Per-page maximum, explicit exemptions", "mechanical"),
    "P06": ("Contents, tables, section size", "mechanical"),
    "P07": ("No dangling links or anchors", "mechanical"),
    "P08": ("Fixed confidence vocabulary", "semi"),
    "P09": ("Living docs carry no history; archive is not an entry", "mechanical"),
    "P10": ("One authority per fact", "semi"),
    "P11": ("A single-source claim must have no copies", "semi"),
    "P12": ("Decision ledger: four fields, closed status set", "mechanical"),
    "P13": ("Open items are consumable", "semi"),
    "P14": ("Exactly one machine-readable state pointer", "mechanical"),
    "P15": ("Only re-derive commands for changing values", "mechanical"),
    "P16": ("Append-only session logs", "mechanical"),
    "P17": ("Write-back names file, section, and trigger", "semi"),
    "P18": ("A check entry point in the workspace", "mechanical"),
    "P19": ("Irreversible operations, with failure modes", "semi"),
    "P20": ("Conclusion wording discipline", "manual"),
    "P21": ("Cold-start budget, single routing table", "mechanical"),
    "P22": ("Evidence resolves (file exists, line in range)", "mechanical"),
}

# Tiers: enable by scale, so small projects do not carry all 22 principles
TIERS = {
    "L0": ["P01", "P04", "P14", "P15", "P16", "P18"],
    "L1": ["P01", "P02", "P04", "P05", "P07", "P13", "P14", "P15", "P16", "P17", "P18", "P22"],
    "L2": [f"P{n:02d}" for n in range(1, 23)],
}

MANUAL_HINTS = {
    "P03": "Does the child only implement, without relaxing a parent never into prefer? Did it copy the parent list instead of linking?",
    "P08": "Sample three conclusions: is [inferred] ever stated as fact; does every upgrade carry new evidence?",
    "P10": "Review the near-duplicate sentence pairs; the same fact twice should become a link",
    "P11": "Outside the single-authority declaration, are there still status claims? (the script counts volatile ones only)",
    "P13": "Sample three open items: is the status real; does a resolved item keep its row?",
    "P17": "Is every write-back obligation actually triggerable (hook / CI / closing script), not just written down?",
    "P19": "Are the prohibitions specific to this project (not 'do not commit secrets'), and do they carry a failure mode?",
    "P20": "Did the capability boundary actually prevent conclusions; does the checklist have a criterion column and a fallback?",
}

# ---------------------------------------------------------------- helpers

CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff]")
PUNCT = re.compile(r"[^\w\s\-]", re.UNICODE)
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
HEAD = re.compile(r"^(#{1,6})\s+(.*)$")
EVIDENCE = re.compile(
    r"`([^`\s]+?\.(?:md|mdx|json|ya?ml|py|sh|ps1|sv|svh|v|c|h|ld|f|ini|csh|toml|log|txt|csv))"
    r":(\d+)(?:-(\d+))?`"
)

INLINE_PATH = re.compile(
    r"`([^`\s]{2,140}\.(?:md|mdx|json|ya?ml|py|sh|ps1|sv|svh|c|h|ld|f|ini|csh|toml))"
    r"(?::\d+(?:-\d+)?|#[^`\s]*)?`"
)


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def nlines(text: str) -> int:
    return len(text.splitlines())


def slug(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"\*\*|__|~~", "", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = t.replace("`", "")
    t = PUNCT.sub("", t)
    return re.sub(r"\s", "-", t.strip())


def heading_slugs(text: str) -> set:
    out = set()
    for line in text.splitlines():
        m = HEAD.match(line.strip())
        if m:
            out.add(slug(m.group(2)))
    return out


def is_archive(path: Path, root: Path, cfg) -> bool:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return False
    if re.search(r"(^|/)_?archive[^/]*/", rel, re.I):
        return True
    return any(rel.startswith(d.strip("/") + "/") or rel == d.strip("/") for d in cfg["archive_dirs"])


def category(name: str) -> str:
    low = name.lower()
    if re.search(r"(^|_)00[_-]|index", low):
        return "index"
    if re.search(r"inventory|change|amend", low):
        return "inventory"
    if re.search(r"pitfall|trouble|troubleshoot", low):
        return "pitfalls"
    return "default"


def walk_files(root: Path, cfg, max_depth=None):
    """Walk the tree pruning skip_dirs; max_depth counts levels below root (None = unlimited)."""
    skip = set(cfg["skip_dirs"])
    base = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).parts) - base
        dirnames[:] = [d for d in dirnames if d not in skip]
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        for fn in filenames:
            yield Path(dirpath) / fn


def doc_roots(root: Path, cfg):
    names = cfg["docs_root"] if isinstance(cfg["docs_root"], list) else [cfg["docs_root"]]
    return [root / n for n in names if (root / n).is_dir()]


def iter_docs(root: Path, cfg):
    """(path, text, is_archive) - document roots plus entry files, skipping noise directories.

    Without docs/ or notes/ this degrades to a shallow workspace scan (depth <= 2),
    so a plain folder or a non-code workspace can still be audited.
    """
    seen, out = set(), []
    targets = [(r, True) for r in doc_roots(root, cfg)] or [(root, True)]
    for name in cfg["entry_files"]:
        p = root / name
        if p.is_file():
            targets.append((p, False))
        for sub in root.glob(f"*/{name}"):
            if sub.is_file():
                targets.append((sub, False))

    for t, is_dir in targets:
        if not is_dir:
            files = [t]
        else:
            files = sorted(t.rglob("*.md"))
            if t == root:
                files = [f for f in files if len(f.relative_to(root).parts) <= 2]
        for f in files:
            if f in seen or not f.is_file():
                continue
            if any(part in cfg["skip_dirs"] for part in f.parts):
                continue
            seen.add(f)
            out.append((f, read(f), is_archive(f, root, cfg)))
    return sorted(out, key=lambda x: x[0].as_posix())


def tables(text: str):
    """Yield (header_cells, rows) for each markdown table."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            yield header, rows
            i = j
        else:
            i += 1


def sections(text: str):
    """Yield (title, start_line, body_lines)."""
    lines = text.splitlines()
    starts = [(idx, HEAD.match(l.strip())) for idx, l in enumerate(lines)]
    starts = [(i, m) for i, m in starts if m and m.group(1) == "##"]
    for k, (i, m) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        yield m.group(2).strip(), i + 1, lines[i + 1:end]


def est_tokens(text: str) -> int:
    cjk = len(CJK.findall(text))
    other = len(text) - cjk
    return int(cjk + other / 4)


# ---------------------------------------------------------------- auditor

class Audit:
    def __init__(self, root: Path, cfg):
        self.root = root
        self.cfg = cfg
        self.findings = []       # dict(id, level, msg, locs)
        self.notes = []
        self.tier = (cfg.get("tier") or "L2").upper()
        if self.tier not in TIERS:
            self.tier = "L2"
        self.active = set(TIERS[self.tier])
        self.docs = iter_docs(root, cfg)
        self.entries = [root / n for n in cfg["entry_files"] if (root / n).is_file()]
        self.entry = self.entries[0] if self.entries else None
        self.entry_text = read(self.entry) if self.entry else ""
        self.top_index = self._find_top_index()

    def _find_top_index(self):
        roots = doc_roots(self.root, self.cfg) or [self.root]
        for dr in roots:
            for probe in ("00_INDEX.md", "README.md", "*INDEX*.md", "index.md"):
                import fnmatch
                hits = [h for h in walk_files(dr, self.cfg, max_depth=3)
                        if fnmatch.fnmatch(h.name, probe)]
                if hits:
                    return sorted(hits, key=lambda h: (len(h.relative_to(dr).parts), h.as_posix()))[0]
        return None

    def _tails(self):
        """Map every file name and its last one/two path segments to paths (pruned walk, capped)."""
        if getattr(self, "_tailmap", None) is None:
            m = {}
            skip = set(self.cfg["skip_dirs"])
            cap = int(self.cfg.get("suffix_index_cap", 300000))
            for dirpath, dirnames, filenames in os.walk(self.root):
                dirnames[:] = [d for d in dirnames if d not in skip]
                rel = os.path.relpath(dirpath, self.root)
                parts = [] if rel == "." else rel.replace("\\", "/").split("/")
                for fn in filenames:
                    full = os.path.join(dirpath, fn)
                    keys = [fn]
                    if parts:
                        keys.append(parts[-1] + "/" + fn)
                    if len(parts) >= 2:
                        keys.append("/".join(parts[-2:] + [fn]))
                    for k in keys:
                        m.setdefault(k, []).append(full)
                if len(m) > cap:
                    break
            self._tailmap = m
        return self._tailmap

    def _suffix_index(self):
        return set(self._tails())

    def add(self, pid, level, msg, locs=None):
        self.findings.append({"id": pid, "level": level, "msg": msg, "locs": locs or []})

    def _discover(self, names, default_rel):
        """Find a config file: default relative path first, then same-named files under root or the docs root."""
        p = self.root / default_rel
        if p.is_file():
            return p
        import fnmatch
        hits = []
        for d in [self.root] + doc_roots(self.root, self.cfg):
            for h in walk_files(d, self.cfg, max_depth=None if d != self.root else 4):
                if h.name in names or any(fnmatch.fnmatch(h.name, n) for n in names if "*" in n):
                    if not is_archive(h, self.root, self.cfg):
                        hits.append(h)
        return sorted(hits)[0] if hits else None

    # ---------------- P01
    def p01(self):
        if not self.entries:
            self.add("P01", "FAIL", f"No entry file at the workspace root (expected one of {self.cfg['entry_files']})")
            return
        limit = self.cfg["limits"]["default"]
        for e in self.entries:
            n = nlines(read(e))
            lvl = "PASS" if n <= limit else "FAIL"
            self.add("P01", lvl, f"{e.name}: {n} lines (limit {limit})")
        head = "\n".join(self.entry_text.splitlines()[:10])
        if not re.search(r"entry|only|read this first", head, re.I):
            self.add("P01", "WARN", "The first 10 lines do not declare 'only entry / read this first'")

    # ---------------- P02
    def p02(self):
        if not self.entry:
            self.add("P02", "FAIL", "No entry file; cannot judge routing")
            return
        ok_rows = 0
        for header, rows in tables(self.entry_text):
            joined = " ".join(header) + " " + " ".join(c for r in rows for c in r)
            if len(rows) >= self.cfg["routing_min_rows"] and re.search(r"read|see|->|\u2192", joined, re.I):
                ok_rows = max(ok_rows, len(rows))
        if ok_rows:
            self.add("P02", "PASS", f"Routing table present ({ok_rows} rows)")
        else:
            self.add("P02", "FAIL", f"No intent-to-document table with at least {self.cfg['routing_min_rows']} rows in the entry")
        if not re.search(r"do not read in order|on demand|one page only|by intent", self.entry_text, re.I):
            self.add("P02", "WARN", "The entry does not say 'do not read in order'")

    # ---------------- P03
    def p03(self):
        nested = [(p, t) for p, t, _ in self.docs if p.name in self.cfg["entry_files"] and p != self.entry]
        if not nested:
            self.add("P03", "PASS", "No child entry files (single-layer structure)")
            return
        parent = self.entry.name if self.entry else ""
        missing = [str(p) for p, t in nested if parent and parent not in t]
        if missing:
            self.add("P03", "WARN", "A child entry does not link back to the parent entry", missing[:5])
        else:
            self.add("P03", "PASS", f"{len(nested)} child entry file(s), all link back to the parent")

    # ---------------- P04
    def p04(self):
        patterns = [
            ("HEAD literal", re.compile(r"\bHEAD\b[^\n|]{0,24}\b[0-9a-f]{7,40}\b")),
            ("commit literal", re.compile(r"(?:commit)[^\n|]{0,16}\b[0-9a-f]{7,40}\b", re.I)),
            ("count expression", re.compile(r"(?<!\d)[×]\s*\d+")),
            ("item-count status", re.compile(r"\d+\s*(?:uncommitted|untracked|changed|items?|commits?|files?)\s*[`\s]*(?:uncommitted|untracked|changed|items?|commits?|files?|M\b|\?\?)", re.I)),
            ("exactly-N claim", re.compile(r"(?:exactly|only)\s*\d+", re.I)),
            ("git status count", re.compile(r"status --porcelain[^\n]{0,40}\d+")),
            ("commit count", re.compile(r"\d+\s*(?:commits?|entries)", re.I)),
            ("file/line count", re.compile(r"\d+\s*files?[^\n]{0,12}\d{2,}\s*lines?", re.I)),
            ("current plus number", re.compile(r"(?:current|currently|latest|as of)[^\n]{0,12}\d+\s*(?:items?|files?|commits?|entries)", re.I)),
            ("progress percentage", re.compile(r"\d{1,3}\s*%\s*(?:done|complete|completed|finished)", re.I)),
            ("version literal", re.compile(r"(?:latest|current)\s*version[^\n]{0,8}v?\d+\.\d+", re.I)),
        ]
        targets = []
        if "entry" in self.cfg["volatile_scope"]:
            targets += [(e, read(e)) for e in self.entries]
        if "index" in self.cfg["volatile_scope"] and self.top_index:
            targets.append((self.top_index, read(self.top_index)))
        hits = []
        if not targets:
            self.add("P04", "UNKNOWN", "No entry or index to scan (create the entry first)")
            return
        for p, t in targets:
            for i, line in enumerate(t.splitlines(), 1):
                for name, rx in patterns:
                    m = rx.search(line)
                    if m:
                        hits.append(f"{p.relative_to(self.root).as_posix()}:{i} [{name}] {m.group(0)[:40]}")
        if hits:
            self.add("P04", "FAIL", f"{len(hits)} volatile value(s) in the resident layer (replace with re-derive commands)", hits[:20])
        else:
            self.add("P04", "PASS", "No volatile facts in the resident layer")

    # ---------------- P05
    def p05(self):
        over, exempt = [], set(self.cfg["exempt_files"])
        for p, t, arch in self.docs:
            if arch:
                continue
            rel = p.relative_to(self.root).as_posix()
            if rel in exempt or p.name in exempt:
                continue
            cat = category(p.name)
            limit = self.cfg["limits"].get(cat, self.cfg["limits"]["default"]) \
                if cat in self.cfg["exempt_categories"] else self.cfg["limits"]["default"]
            n = nlines(t)
            if n > limit:
                over.append(f"{rel}: {n}/{limit} lines (category {cat})")
        if over:
            self.add("P05", "FAIL", f"{len(over)} page(s) over the line limit", over[:15])
        else:
            self.add("P05", "PASS", f"{len(self.docs)} page(s) within the limits")

        # Floor: prevent shredding a coherent topic just to pass the cap
        short = []
        floor = int(self.cfg.get("min_doc_lines", 15))
        for p, t, arch in self.docs:
            if arch or category(p.name) == "index":
                continue
            rel = p.relative_to(self.root).as_posix()
            if rel.startswith(self.cfg["session_dir"].strip("/") + "/") or p.name.lower().startswith("decisions"):
                continue
            n = nlines(t)
            if 0 < n < floor:
                short.append(f"{rel}: {n}/{floor} lines")
        if short:
            self.add("P05", "WARN", f"{len(short)} page(s) shorter than {floor} lines (check for fragmentation)", short[:10])

    # ---------------- P06
    def p06(self):
        no_toc, heavy = [], []
        for p, t, arch in self.docs:
            if arch or p.name in self.cfg["entry_files"]:
                continue
            lines = t.splitlines()
            if len(lines) < 30:
                continue
            head = "\n".join(lines[:40])
            if not re.search(r"^#{1,6}\s*(Contents|TOC)", head, re.M):
                no_toc.append(p.relative_to(self.root).as_posix())
            elif len(re.findall(r"\]\(#", head)) < 3:
                no_toc.append(p.relative_to(self.root).as_posix() + "(contents anchors < 3)")
            if category(p.name) == "default":
                for title, start, body in sections(t):
                    if len(body) > self.cfg["section_max_lines"]:
                        heavy.append(f"{p.relative_to(self.root).as_posix()}:{start} section {title[:20]} is {len(body)} lines")
        if no_toc:
            self.add("P06", "FAIL", f"{len(no_toc)} page(s) missing contents or anchors", no_toc[:12])
        else:
            self.add("P06", "PASS", "All pages have a contents block")
        if heavy:
            self.add("P06", "WARN", f"{len(heavy)} section(s) over {self.cfg['section_max_lines']} lines", heavy[:10])

    # ---------------- P07
    def p07(self):
        missing, bad_anchor, unresolved = [], [], []
        cache = {}
        for p, t, arch in self.docs:
            if arch:
                continue
            base = p.parent
            for m in LINK.finditer(t):
                raw = m.group(1).strip()
                if raw.startswith(("http://", "https://", "mailto:", "#")) or re.fullmatch(r":[\d\-]+[\w\-]*", raw):
                    continue
                path_part, _, anchor = raw.partition("#")
                target = (base / path_part).resolve() if path_part else p
                if path_part and not target.exists():
                    missing.append(f"{p.relative_to(self.root).as_posix()} → {raw}")
                    continue
                if anchor and target.suffix.lower() in (".md", ".mdx") and target.is_file():
                    if target not in cache:
                        cache[target] = heading_slugs(read(target))
                    if anchor not in cache[target]:
                        bad_anchor.append(f"{p.relative_to(self.root).as_posix()} → {raw}")
            if self.cfg["check_inline_paths"]:
                bases = [base]
                cur = base
                while cur != cur.parent and self.root in cur.parents:
                    bases.append(cur.parent)
                    cur = cur.parent
                bases.append(self.root)
                bases += [Path(r) for r in self.cfg.get("alt_roots") or []]
                for m in INLINE_PATH.finditer(t):
                    cand = m.group(1).lstrip("./")
                    if not re.search(r"[/\\]", cand):
                        continue
                    if any((b / cand).exists() for b in bases):
                        continue
                    segs = cand.replace("\\", "/").split("/")
                    tail = "/".join(segs[-2:]) if len(segs) >= 2 else segs[-1]
                    if tail in self._suffix_index():
                        continue
                    unresolved.append(f"{p.relative_to(self.root).as_posix()} → `{cand}`")
        if missing:
            self.add("P07", "FAIL", f"{len(missing)} link(s) point at missing files", missing[:15])
        else:
            self.add("P07", "PASS", "No dangling relative links")
        if bad_anchor:
            self.add("P07", "FAIL", f"{len(bad_anchor)} anchor(s) do not resolve", bad_anchor[:15])
        if unresolved:
            self.add("P07", "WARN", f"{len(unresolved)} inline path(s) unresolved (may be relative to another root)",
                     unresolved[: self.cfg["inline_path_max_reports"]])

    # ---------------- P08
    def p08(self):
        bad, zero = [], []
        markers = list(self.cfg["markers"].values())
        for p, t, arch in self.docs:
            if arch:
                continue
            for v in self.cfg["forbidden_marker_variants"]:
                for line in t.splitlines():
                    if v in line and not re.search(r"forbidden|synonym|variant", line, re.I):
                        bad.append(f"{p.relative_to(self.root).as_posix()} contains an unknown marker {v}")
            rel = p.relative_to(self.root).as_posix()
            is_record = rel.startswith(self.cfg["session_dir"].strip("/") + "/")                 or rel == self.cfg["decisions_file"].strip("/") or p.name.lower().startswith("decisions")
            if category(p.name) != "index" and not is_record and not any(mk in t for mk in markers):
                zero.append(rel)
        counts = {k: sum(t.count(v) for _, t, _ in self.docs) for k, v in self.cfg["markers"].items()}
        if bad:
            self.add("P08", "FAIL", "Marker variants outside the configured vocabulary", bad[:10])
        else:
            self.add("P08", "PASS", "Marker vocabulary stable; " +
                     " / ".join(f"{k}={v}" for k, v in counts.items()))
        if zero:
            self.add("P08", "WARN", f"{len(zero)} page(s) carry no confidence marker", zero[:10])

    # ---------------- P09
    def p09(self):
        refs = []
        for p, t, arch in self.docs:
            if arch:
                continue
            for m in LINK.finditer(t):
                raw = m.group(1)
                if any(d.split("/")[-1] in raw for d in self.cfg["archive_dirs"]):
                    refs.append((p.relative_to(self.root).as_posix(), raw))
        entry_refs = [f"{a} → {b}" for a, b in refs if self.entry and a == self.entry.name]
        other_refs = [f"{a} → {b}" for a, b in refs if not (self.entry and a == self.entry.name)]
        if entry_refs:
            self.add("P09", "FAIL", "The entry links to the archive (archives must not be an entry)", entry_refs[:5])
        elif other_refs:
            self.add("P09", "WARN", f"{len(other_refs)} live-document link(s) point at the archive (allowed only as history references)", other_refs[:8])
        else:
            self.add("P09", "PASS", "No live document references the archive")

    # ---------------- P10
    def p10(self):
        sents = []      # (file, lineno, norm)
        fence = False
        for p, t, arch in self.docs:
            if arch:
                continue
            rel = p.relative_to(self.root).as_posix()
            if rel.startswith(self.cfg["session_dir"].strip("/") + "/") or p.name.lower().startswith("decisions"):
                continue
            for i, line in enumerate(t.splitlines(), 1):
                if line.strip().startswith("```"):
                    fence = not fence
                    continue
                if fence or line.lstrip().startswith(("|", "#", ">")) and not line.lstrip().startswith(">"):
                    continue
                for part in re.split(r"[。；;！？!?]", line):
                    norm = PUNCT.sub("", part.strip()).lower()
                    if len(norm) >= 15:
                        sents.append((p.relative_to(self.root).as_posix(), i, norm))
        grams = {}
        for idx, (_, _, norm) in enumerate(sents):
            for g in {norm[i:i + 3] for i in range(len(norm) - 2)}:
                grams.setdefault(g, []).append(idx)

        counts = {}
        for post in grams.values():
            if len(post) < 2 or len(post) > 60:
                continue
            for a in range(len(post)):
                for b in range(a + 1, len(post)):
                    ka, kb = post[a], post[b]
                    if sents[ka][0] == sents[kb][0]:
                        continue
                    key = (ka, kb)
                    counts[key] = counts.get(key, 0) + 1

        thr = self.cfg["similarity_threshold"]
        pairs = []
        for (ka, kb), shared in counts.items():
            na, nb = sents[ka][2], sents[kb][2]
            jac = shared / (len(na) + len(nb) - shared)
            if jac >= thr:
                pairs.append((round(jac, 2), f"{sents[ka][0]}:{sents[ka][1]}", f"{sents[kb][0]}:{sents[kb][1]}",
                              na[:38]))
        pairs.sort(reverse=True)
        if pairs:
            self.add("P10", "WARN", f"{len(pairs)} near-duplicate sentence pair(s) may be the same fact (human review)",
                     [f"{j} {a} ≈ {b}  「{s}…」" for j, a, b, s in pairs[: self.cfg["dup_max_reports"]]])
        else:
            self.add("P10", "PASS", "No cross-file near-duplicate sentences")

    # ---------------- P11
    def p11(self):
        decl = None
        for p, t, arch in self.docs:
            if arch or category(p.name) != "index" and p != self.entry:
                continue
            for i, line in enumerate(t.splitlines(), 1):
                if re.search(r"single source of truth|only entry|single authority", line, re.I):
                    decl = (p.relative_to(self.root).as_posix(), i, line.strip()[:70])
                    break
            if decl:
                break
        if not decl:
            self.add("P11", "UNKNOWN", "No single-authority declaration found (ignore if not needed)")
            return
        # Reuse the P04 result: are there still volatile claims outside the declaration?
        fails = [f for f in self.findings if f["id"] == "P04" and f["level"] == "FAIL"]
        n_outside = len([l for l in (fails[0]["locs"] if fails else []) if not l.startswith(decl[0])])
        lvl = "WARN" if n_outside else "PASS"
        self.add("P11", lvl, f"Declared at {decl[0]}:{decl[1]}; {n_outside} volatile claim(s) outside it")

    # ---------------- P12
    def p12(self):
        p = self._discover(["decisions.md", "decisions*.md", "adr*.md", "DECISIONS.md"],
                           self.cfg["decisions_file"])
        if p is None:
            self.add("P12", "FAIL", f"Missing decision ledger {self.cfg['decisions_file']}")
            return
        t = read(p)
        allowed = set(self.cfg.get("decision_statuses") or
                      ["adopted", "rejected", "failed", "pending"])
        ok_table, rows_total, bad_status, no_reason = False, 0, [], []
        for header, rows in tables(t):
            hlow = [h.lower() for h in header]
            has = sum(any(k in h for k in ("Decision", "Status", "Reason", "Evidence", "decision", "status", "rationale", "evidence"))
                      for h in hlow)
            if not (len(rows) >= 2 and has >= 3):
                continue
            ok_table = True
            idx = {k: next((i for i, h in enumerate(header) if k in h.lower()), None)
                   for k in ("Status", "Reason", "Evidence")}
            for r in rows:
                rows_total += 1
                if idx["Status"] is not None and idx["Status"] < len(r):
                    st = r[idx["Status"]]
                    if not any(a in st for a in allowed):
                        bad_status.append(st[:24])
                if "rejected" in " ".join(r):
                    if idx["Reason"] is not None and idx["Reason"] < len(r) and len(r[idx["Reason"]]) < 6:
                        no_reason.append(" | ".join(r)[:50])
        if not ok_table:
            self.add("P12", "FAIL", "The decision ledger has no decision/status/reason/evidence table")
            return
        lvl = "PASS" if not bad_status else "WARN"
        self.add("P12", lvl, f"{rows_total} decision(s); {len(bad_status)} status value(s) outside the closed set (extend decision_statuses)",
                 bad_status[:8])
        if no_reason:
            self.add("P12", "WARN", "rejected row without a reason", no_reason[:8])

    # ---------------- P13 / P14 / P15
    def _state(self):
        cands = [self.root / self.cfg["state_file"], self.root / "STATE.json",
                 self.root / "docs" / "STATE.json", self.root / "notes" / "STATE.json"]
        p = next((c for c in cands if c.is_file()), None)
        if p is None:
            hits = [h for h in walk_files(self.root, self.cfg, max_depth=3) if h.name == "STATE.json"]
            p = sorted(hits)[0] if hits else None
        if not p:
            return None, None
        raw = read(p)
        if p.suffix.lower() == ".json":
            try:
                return p, json.loads(raw)
            except json.JSONDecodeError:
                return p, None
        # YAML: no full parse, just top-level keys - enough for P14 key completeness
        keys = set(re.findall(r"^([A-Za-z_][\w-]*)\s*:", raw, re.M))
        return p, ({k: True for k in keys} if keys else None)

    def p13(self):
        p, state = self._state()
        rows = state.get("opens") if isinstance(state, dict) else None
        if rows is None:
            op = self._discover(["opens.md", "OPEN*.md", "blockers.md"], self.cfg["opens_file"])
            if op is None:
                self.add("P13", "FAIL", "Neither STATE.opens nor an opens file exists")
                return
            rows = [r for _, rr in tables(read(op)) for r in rr]
        if not isinstance(rows, list) or not rows:
            self.add("P13", "FAIL", "opens is empty")
            return
        need = {"id", "status", "next_action", "evidence"}
        bad = [str(r)[:40] for r in rows if isinstance(r, dict) and not need.issubset(r)]
        allowed = {"open", "blocked", "done", "dropped", "pending", "in-progress", "resolved"}
        bad_st = [str(r.get("status")) for r in rows if isinstance(r, dict) and r.get("status") not in allowed]
        lvl = "PASS" if not bad and not bad_st else "WARN"
        self.add("P13", lvl, f"{len(rows)} open item(s); {len(bad)} missing field(s); {len(bad_st)} bad status value(s)")

    def p14(self):
        p, state = self._state()
        if not p:
            self.add("P14", "FAIL", f"Missing state file {self.cfg['state_file']}")
            return
        if state is None:
            self.add("P14", "FAIL", f"{self.cfg['state_file']} is not parseable (JSON only)")
            return
        need = {"schema_version", "updated_at", "phase", "opens", "next_action"}
        miss = need - set(state)
        self.add("P14", "PASS" if not miss else "FAIL",
                 "State file keys complete" if not miss else f"Missing keys {sorted(miss)}")

    def p15(self):
        p, state = self._state()
        if not isinstance(state, dict):
            self.add("P15", "UNKNOWN", "No state file; skipped")
            return
        has_cmd = bool(state.get("commands") or state.get("derive_cmd"))
        ts = state.get("derived_at")
        age = None
        if ts:
            try:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - dt).days
            except ValueError:
                age = None
        lvl = "PASS" if has_cmd and age is not None else "WARN"
        if not has_cmd:
            self.add("P15", "FAIL", "State file lacks commands (changing values must be re-derivable)")
        if age is None:
            self.add("P15", "WARN", "derived_at missing or unparseable")
        elif age > self.cfg["stale_days"]:
            self.add("P15", "WARN", f"derived_at is {age} day(s) old; run commands first")
        else:
            self.add("P15", lvl, f"derived_at is {age} day(s) old; commands present")

        # Projection reconciliation: STATE names the session it was derived from
        sd = self.root / self.cfg["session_dir"]
        if sd.is_dir():
            logs = [f for f in sd.glob("*.md") if f.name.lower() != "index.md"]
            newest = max(logs, key=lambda f: (f.name, f.stat().st_mtime), default=None)
            last = state.get("last_session")
            lag = float(self.cfg.get("state_lag_hours", 24)) * 3600
            try:
                upd_ts = datetime.fromisoformat(str(state.get("updated_at")).replace("Z", "+00:00")).timestamp()
            except (ValueError, TypeError):
                upd_ts = None
            if newest is not None:
                if last and last not in newest.stem:
                    self.add("P15", "WARN", f"STATE.last_session={last} but the newest session is {newest.stem} (projection not updated)")
                elif not last and upd_ts and newest.stat().st_mtime > upd_ts + lag:
                    self.add("P15", "WARN", "STATE lags the newest session log (rebuild the projection; see the bootstrap opening step)")

    # ---------------- P16
    def p16(self):
        d = self.root / self.cfg["session_dir"]
        if not d.is_dir():
            self.add("P16", "FAIL", f"Missing session directory {self.cfg['session_dir']}")
            return
        logs = [p for p in d.glob("*.md") if p.name.lower() != "index.md"]
        bad_name = [p.name for p in logs if not re.match(r"\d{4}-\d{2}-\d{2}", p.name)]
        long = [f"{p.name}: {nlines(read(p))} lines" for p in logs if nlines(read(p)) > 20]
        has_index = any(p.name.lower() == "index.md" for p in d.glob("*.md"))
        probs = []
        if bad_name:
            probs.append(f"{len(bad_name)} session file(s) without a date prefix")
        if long:
            probs.append(f"{len(long)} session file(s) over 20 lines")
        if not has_index:
            probs.append("Missing INDEX.md")
        self.add("P16", "PASS" if not probs else "FAIL",
                 f"{len(logs)} session log(s)" + ("；" + "；".join(probs) if probs else ""),
                 (bad_name[:5] + long[:5]))

    # ---------------- P17
    def p17(self):
        if not self.entry:
            self.add("P17", "FAIL", "No entry file")
            return
        hits = [(title, body) for title, _, body in sections(self.entry_text)
                if re.search(r"write-?back|closing|update.*docs?", title, re.I)]
        if not hits:
            self.add("P17", "FAIL", "The entry has no write-back obligations section")
        else:
            body = "\n".join("\n".join(b) for _, b in hits)
            refs = re.findall(r"[\w\-./]+\.(?:md|json|ya?ml)", body)
            trig = self._trigger_exists()
            lvl = "PASS" if refs and trig else "WARN"
            self.add("P17", lvl,
                     f"Write-back obligations reference {len(refs)} concrete file(s); trigger {'present' if trig else 'not found'}")

    def _trigger_exists(self):
        if (self.root / ".pre-commit-config.yaml").is_file():
            return True
        if (self.root / ".github" / "workflows").is_dir():
            return True
        for cand in ("Makefile", "makefile", "Justfile", "package.json"):
            p = self.root / cand
            if p.is_file() and re.search(r"check|audit|lint", read(p), re.I):
                return True
        hooks = self.root / ".git" / "hooks"
        if hooks.is_dir() and any(h.is_file() and h.stat().st_size > 0 and h.suffix != ".sample"
                                  for h in hooks.iterdir()):
            return True
        if list(self.root.glob("scripts/check*")) or list(self.root.glob("tools/check*"))                 or list(self.root.glob("tools/audit*")) or list(self.root.glob("scripts/audit*")):
            return True
        return (self.root / "audit.py").is_file()

    # ---------------- P18
    def p18(self):
        cands = [
            *self.root.glob("tools/audit*"), *self.root.glob("scripts/audit*"),
            *self.root.glob("tools/check*"), *self.root.glob("scripts/check*"),
            self.root / "tools" / "audit.py",
        ]
        for pat in ("*.py", "*.sh", "*.ps1", "*.bat", "*.cmd"):
            for c in self.root.glob(pat):
                if re.match(r"(audit|check)[\w.-]*\.(py|sh|ps1|bat|cmd)$", c.name, re.I):
                    cands.append(c)
        exe = {".py", ".sh", ".ps1", ".bat", ".cmd"}
        found = sorted({c for c in cands if c.is_file() and (c.suffix.lower() in exe or c.name in ("Makefile", "makefile"))})
        mk = self.root / "Makefile"
        if mk.is_file() and re.search(r"^check[\w-]*\s*:", read(mk), re.M):
            found.append(mk)
        wf = self.root / ".github" / "workflows"
        if wf.is_dir() and any(re.search(r"audit|check", read(f), re.I) for f in wf.glob("*.y*ml")):
            found.append(wf)
        if found:
            self.add("P18", "PASS", "Check entry point present: " + ", ".join(
                str(c.relative_to(self.root)) for c in found[:3]))
        else:
            self.add("P18", "FAIL", "No single command runs the mechanical checks (script / make target / CI)")

    # ---------------- P19
    def p19(self):
        if not self.entry:
            self.add("P19", "FAIL", "No entry file")
            return
        sec = [(title, "\n".join(body)) for title, _, body in sections(self.entry_text)
               if re.search(r"never|dangerous|hazard|irreversible|do not", title, re.I)]
        if not sec:
            self.add("P19", "FAIL", "The entry has no never/dangerous section")
            return
        body = "\n".join(b for _, b in sec)
        items = [l for l in body.splitlines() if re.match(r"^\s*(?:[-*]|\d+\.|\|)", l)]
        concrete = [l for l in items if re.search(r"`[^`]+`|[/\\]\w+", l)]
        lvl = "PASS" if len(concrete) >= 3 else "WARN"
        self.add("P19", lvl, f"Prohibition list has {len(concrete)} item(s) with a concrete command or path (target >= 3)")

    # ---------------- P20
    def p20(self):
        t = self.entry_text
        has = bool(re.search(r"capability boundary|cannot|limitation", t, re.I))
        has_check = bool(re.search(r"verification|checklist|on hardware", t, re.I))
        self.add("P20", "PASS" if has and has_check else "WARN",
                 f"Capability boundary section {'present' if has else 'missing'}; verification checklist {'present' if has_check else 'missing'} (wording needs human review)")

    # ---------------- P21
    def p21(self):
        if not self.entry:
            self.add("P21", "FAIL", "No entry file")
            return
        parts = [read(e) for e in self.entries]
        p, state = self._state()
        if p:
            parts.append(read(p))
        if self.top_index:
            parts.append(read(self.top_index))
        total = sum(est_tokens(x) for x in parts)
        lvl = "PASS" if total <= self.cfg["budget_tokens"] else "FAIL"
        self.add("P21", lvl, f"Cold-start estimate ~{total} tokens (budget {self.cfg['budget_tokens']})")

        def routing_tables(text):
            n = 0
            for header, rows in tables(text):
                if len(rows) < 3:
                    continue
                if sum(1 for r in rows if any(re.search(r"\]\(|`[^`]+\.(?:md|mdx)`", c) for c in r)) >= 3 and re.search(
                        r"I want|want to|intent|goal", " ".join(header + [c for r in rows[:2] for c in r]), re.I):
                    n += 1
            return n

        n_tables = routing_tables(self.entry_text) + (routing_tables(read(self.top_index)) if self.top_index else 0)
        if n_tables >= 2:
            self.add("P21", "FAIL", f"{n_tables} routing table(s) found (keep only the entry one)")
        else:
            self.add("P21", "PASS", f"{n_tables} routing table(s)")

    # ---------------- P22
    def p22(self):
        missing, bad = [], []
        roots_rel = {r.relative_to(self.root).as_posix() for r in doc_roots(self.root, self.cfg)}
        strict_prefixes = tuple(sorted(roots_rel)) or ("docs/",)
        for p, t, arch in self.docs:
            if arch:
                continue
            base = p.parent
            bases, cur = [base], base
            while cur != cur.parent and self.root in cur.parents:
                bases.append(cur.parent)
                cur = cur.parent
            bases.append(self.root)
            bases += [Path(r) for r in self.cfg.get("alt_roots") or []]
            for m in EVIDENCE.finditer(t):
                target, start = m.group(1), int(m.group(2))
                end = int(m.group(3) or start)
                segs = target.replace("\\", "/").split("/")
                tail = "/".join(segs[-2:]) if len(segs) >= 2 else segs[-1]
                cand, exact = None, True
                for b in bases:
                    if (b / target).is_file():
                        cand = b / target
                        break
                if cand is None:
                    hits = self._tails().get(tail) or self._tails().get(segs[-1])
                    if hits:
                        cand, exact = Path(hits[0]), False
                rel = p.relative_to(self.root).as_posix()
                if cand is None:
                    strict = target.replace("\\", "/").startswith(strict_prefixes)
                    item = f"{rel} → `{target}:{start}`"
                    (bad if strict else missing).append(item)
                    continue
                n = nlines(read(cand))
                if end > n or start < 1:
                    item = f"{rel} -> {target}:{start}-{end}, local same-name file has {n} lines"
                    # Only exact relative resolutions count as hard errors; same-name versions only warn
                    (bad if exact else missing).append(item)
        bad = list(dict.fromkeys(bad))
        missing = list(dict.fromkeys(missing))
        if bad:
            self.add("P22", "FAIL", f"{len(bad)} evidence citation(s) unresolved or out of range", bad[: self.cfg["evidence_max_reports"]])
        elif not missing:
            self.add("P22", "PASS", "All in-workspace evidence resolves")
        if missing:
            self.add("P22", "WARN", f"{len(missing)} evidence citation(s) point outside the workspace (confirm they are external logs)",
                     missing[: self.cfg["evidence_max_reports"]])

    # ---------------- run
    def run(self, only=None, tier=None):
        if tier:
            self.tier = tier.upper() if tier.upper() in TIERS else "L2"
            self.active = set(TIERS[self.tier])
        active = set(self.active)
        if only:
            active &= only
        methods = [f"p{n:02d}" for n in range(1, 23)]
        for name in methods:
            pid = "P" + name[1:]
            if pid not in active:
                continue
            try:
                getattr(self, name)()
            except Exception as exc:  # a checker bug must not abort the whole run
                self.add(pid, "UNKNOWN", f"Checker error: {type(exc).__name__}: {exc}")
        return self.findings


# ---------------------------------------------------------------- output

LEVEL_ORDER = {"FAIL": 0, "WARN": 1, "UNKNOWN": 2, "PASS": 3}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Progressive knowledge-layer auditor (read-only)")
    ap.add_argument("root", nargs="?", default=".", help="workspace root")
    ap.add_argument("--only", default="", help="run only the listed principles, comma separated, e.g. P04,P07")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--config", default="", help="config file path")
    ap.add_argument("--tier", default="", help="L0 / L1 / L2 (overrides the config tier)")
    ap.add_argument("--quiet", action="store_true", help="print only FAIL/WARN")
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    cfg = dict(DEFAULTS)
    for cand in [Path(args.config) if args.config else None,
                 Path(__file__).with_name("audit.config.json"),
                 root / "tools" / "audit.config.json"]:
        if cand and cand.is_file():
            try:
                cfg.update(json.loads(read(cand)))
            except json.JSONDecodeError as exc:
                print(f"error: cannot parse config {cand}: {exc}", file=sys.stderr)
                return 2
            break

    only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
    auditor = Audit(root, cfg)
    findings = auditor.run(only or None, args.tier or None)
    findings.sort(key=lambda f: (LEVEL_ORDER[f["level"]], f["id"]))

    if args.json:
        print(json.dumps({"root": str(root), "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print(f"workspace: {root}")
        print(f"Tier: {auditor.tier} ({len(auditor.active)}/{len(PRINCIPLES)} principles); "
              f"documents: {len(iter_docs(root, cfg))}\n")
        print(f"{'ID':<5}{'LEVEL':<9}Message")
        print("-" * 78)
        for f in findings:
            if args.quiet and f["level"] in ("PASS",):
                continue
            label = PRINCIPLES.get(f["id"], ("", ""))[0]
            print(f"{f['id']:<5}{f['level']:<9}{f['msg']}")
            if f["level"] != "PASS":
                for loc in f["locs"]:
                    print(f"        - {loc}")
            elif label and args.quiet:
                print(f"        {label}")

        manual = [pid for pid, (_, kind) in PRINCIPLES.items()
                  if kind == "manual" and pid in auditor.active]
        semis = [pid for pid, (_, kind) in PRINCIPLES.items()
                 if kind == "semi" and pid in auditor.active]
        if manual or semis:
            print("Manual checks (the script does not conclude)")
            print("-" * 78)
            for pid in manual + semis:
                if pid in MANUAL_HINTS:
                    print(f"{pid}  {MANUAL_HINTS[pid]}")

        # Aggregate per principle: one principle may emit several rows; keep the worst level
        worst = {}
        for f in findings:
            if f["id"] not in worst or LEVEL_ORDER[f["level"]] < LEVEL_ORDER[worst[f["id"]]]:
                worst[f["id"]] = f["level"]
        cnt = {lv: sum(1 for v in worst.values() if v == lv) for lv in ("FAIL", "WARN", "UNKNOWN", "PASS")}
        print()
        print(f"Total (per principle): FAIL {cnt['FAIL']} - WARN {cnt['WARN']} - "
              f"UNKNOWN {cnt['UNKNOWN']} - PASS {cnt['PASS']}  ({len(worst)} total)")

    return 1 if any(f["level"] == "FAIL" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
