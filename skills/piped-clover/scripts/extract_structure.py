#!/usr/bin/env python3
"""Mechanical parse of pasted research text into a structured JSON skeleton.

Reads raw text from stdin, writes JSON to stdout. The model is expected to
post-edit the JSON to fill semantic gaps (especially narrative and framework
parts) — this script only does deterministic pattern matching.

Schema:
    {
      "title": str,
      "topic_slug_hint": str,
      "word_count": int,
      "sections": [{"heading": str, "bullets": [str], "quotes": [str], "numbers": [{"value": str, "context": str}]}],
      "frameworks": [{"name": str, "parts": [str]}],
      "narrative": {"problem": str, "insight": str, "application": str},
      "evidence": [{"claim": str, "source_span": str}],
      "redactions": int,
      "warnings": [str]
    }
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any

SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"ghp_[a-zA-Z0-9]{30,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}=*"), "Bearer [REDACTED]"),
]

FRAMEWORK_HINTS = re.compile(
    r"\b(?:(?:the\s+)?([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3})\s+(?:framework|model|matrix|canvas|loop|pyramid|principle|method|approach))\b"
)
NUMERIC_CLAIM = re.compile(r"\b(\d+(?:[.,]\d+)?\s*(?:%|percent|x|million|billion|k|bn|m|years?|months?|days?)?)\b", re.I)

# Timestamps at line start: [00:12:34], (12:34), 00:12:34, 12:34, 12:34 -->
TIMESTAMP_RE = re.compile(
    r"^\s*(?:[\[(])?((?:\d{1,2}:)?\d{1,2}:\d{2})(?:[\])])?(?:\s*[-–—>]+)?\s*"
)

# Known research orgs / publications that frequently appear in transcripts.
KNOWN_ORGS = (
    "BCG", "HBS", "MIT", "Harvard", "Stanford", "McKinsey", "Bain", "Gartner",
    "Forrester", "PwC", "Deloitte", "KPMG", "Wharton", "MIT Sloan", "Kellogg",
    "INSEAD", "LSE", "OpenAI", "Anthropic", "DeepMind", "Google Research",
    "Microsoft Research", "NBER", "Brookings", "Pew Research", "OECD",
)
ORG_ALT = "|".join(re.escape(o) for o in KNOWN_ORGS)

REFERENCE_PATTERNS = [
    re.compile(rf"\b(?:a|the|according to|per|from|by)\s+({ORG_ALT})\s+(?:study|report|paper|research|analysis|survey|article|piece|whitepaper)\b", re.I),
    re.compile(rf"\b({ORG_ALT})\s+(?:study|report|paper|research|analysis|survey|article|piece|whitepaper)\b", re.I),
    re.compile(r"\b(?:study|paper|research|report)\s+(?:by|from)\s+([A-Z][A-Za-z\-']+(?:\s+(?:and|&)\s+[A-Z][A-Za-z\-']+)?(?:\s+et\s+al\.?)?)", re.I),
    re.compile(r"\b([A-Z][A-Za-z\-']+\s+et\s+al\.?(?:,?\s+\(?\d{4}\)?)?)", ),
    re.compile(r"\b(?:the\s+)?([A-Z][A-Za-z\-']+(?:\s+[A-Z][A-Za-z\-']+){0,2})\s+(?:\(\d{4}\)|paper|study|report)\b"),
]

NARRATIVE_HEADINGS = {
    "problem": ["problem", "the problem", "pain point", "challenge", "issue", "context"],
    "insight": ["insight", "the insight", "key insight", "core idea", "thesis", "argument"],
    "application": [
        "application",
        "how to apply",
        "takeaway",
        "takeaways",
        "what to do",
        "action",
        "implication",
        "implications",
        "practice",
    ],
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ALT_HEADING_RE = re.compile(r"^([A-Z][^.!?]{4,80})\s*:?\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*+•]|\d+\.)\s+(.+?)\s*$")
QUOTE_RE = re.compile(r"^\s*>\s*(.+?)\s*$")


def parse_timestamp(ts: str) -> int:
    parts = [int(p) for p in ts.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


def strip_timestamp(line: str) -> tuple[str | None, str]:
    m = TIMESTAMP_RE.match(line)
    if not m:
        return None, line
    return m.group(1), line[m.end():]


def detect_references(text: str) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for pattern in REFERENCE_PATTERNS:
        for m in pattern.finditer(text):
            mention = (m.group(1) or "").strip()
            if len(mention) < 2:
                continue
            key = mention.lower()
            if key in seen:
                continue
            seen.add(key)
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 80)
            context = re.sub(r"\s+", " ", text[start:end]).strip()
            search_hint = f'"{mention}" {m.group(0).strip()}'
            found.append({
                "mention": mention,
                "match": m.group(0).strip(),
                "context": context,
                "search_hint": search_hint,
            })
    return found


def redact(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in SECRET_PATTERNS:
        new_text, n = pattern.subn(replacement, text)
        count += n
        text = new_text
    return text, count


def _attach_ts(section: dict[str, Any], ts: str | None) -> None:
    if not ts:
        return
    seconds = parse_timestamp(ts)
    if section.get("start_ts") is None:
        section["start_ts"] = ts
        section["start_seconds"] = seconds


def _new_section(heading: str) -> dict[str, Any]:
    return {
        "heading": heading,
        "bullets": [],
        "quotes": [],
        "numbers": [],
        "start_ts": None,
        "start_seconds": None,
        "bullet_ts": [],
    }


def split_sections(text: str) -> tuple[str, list[dict[str, Any]], bool]:
    lines = text.splitlines()
    title = ""
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    any_timestamp = False

    def flush() -> None:
        if current is not None and (current["bullets"] or current["quotes"] or current["heading"]):
            sections.append(current)

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        ts, line = strip_timestamp(raw_line)
        if ts:
            any_timestamp = True

        m = HEADING_RE.match(line)
        if m:
            level, heading = len(m.group(1)), m.group(2).strip()
            heading_ts, heading = strip_timestamp(heading)
            if heading_ts:
                any_timestamp = True
                ts = ts or heading_ts
            if level == 1 and not title:
                title = heading
            else:
                flush()
                current = _new_section(heading)
                _attach_ts(current, ts)
            i += 1
            continue

        if i + 1 < len(lines) and re.match(r"^[=\-]{3,}\s*$", lines[i + 1]):
            heading = line.strip()
            if lines[i + 1].startswith("=") and not title:
                title = heading
            else:
                flush()
                current = _new_section(heading)
                _attach_ts(current, ts)
            i += 2
            continue

        if current is None:
            am = ALT_HEADING_RE.match(line)
            if am and i + 1 < len(lines) and lines[i + 1].strip() == "":
                current = _new_section(am.group(1).strip())
                _attach_ts(current, ts)
                i += 1
                continue

        if current is None:
            current = _new_section("Overview")
            _attach_ts(current, ts)

        bm = BULLET_RE.match(line)
        if bm:
            bullet_text = bm.group(1).strip()
            inner_ts, bullet_text = strip_timestamp(bullet_text)
            effective_ts = ts or inner_ts
            if effective_ts:
                any_timestamp = True
                _attach_ts(current, effective_ts)
            current["bullets"].append(bullet_text)
            current["bullet_ts"].append(effective_ts)
            i += 1
            continue

        qm = QUOTE_RE.match(line)
        if qm:
            current["quotes"].append(qm.group(1).strip())
            i += 1
            continue

        stripped = line.strip()
        if stripped:
            _attach_ts(current, ts)
            for nm in NUMERIC_CLAIM.finditer(stripped):
                current["numbers"].append({"value": nm.group(1).strip(), "context": stripped[:140]})
            if len(current["bullets"]) < 5:
                if len(stripped) < 300:
                    current["bullets"].append(stripped)
                    current["bullet_ts"].append(ts)
                else:
                    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", stripped) if s.strip()]
                    for s in sentences:
                        if len(current["bullets"]) >= 5:
                            break
                        current["bullets"].append(s[:280])
                        current["bullet_ts"].append(ts)
        i += 1

    flush()
    return title, sections, any_timestamp


def detect_frameworks(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, set[str]] = {}
    for sec in sections:
        blob = " ".join([sec["heading"]] + sec["bullets"] + sec["quotes"])
        for m in FRAMEWORK_HINTS.finditer(blob):
            name = m.group(1).strip()
            if len(name) < 3 or name.lower() in {"the", "this", "that", "a", "an"}:
                continue
            seen.setdefault(name, set())
            for b in sec["bullets"]:
                if name.lower() in b.lower() and len(b) < 200:
                    seen[name].add(b)
    return [{"name": n, "parts": sorted(p)} for n, p in seen.items() if n]


def detect_narrative(sections: list[dict[str, Any]]) -> dict[str, str]:
    narrative = {"problem": "", "insight": "", "application": ""}
    for sec in sections:
        heading_lower = sec["heading"].lower()
        for key, keywords in NARRATIVE_HEADINGS.items():
            if narrative[key]:
                continue
            if any(kw in heading_lower for kw in keywords):
                joined = " ".join(sec["bullets"][:3])
                narrative[key] = joined[:400]
    return narrative


def extract_evidence(sections: list[dict[str, Any]]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for sec in sections:
        for num in sec["numbers"]:
            evidence.append({"claim": num["context"], "source_span": num["value"]})
    return evidence[:20]


def topic_slug_hint(title: str) -> str:
    t = re.sub(r"[^\w\s-]", "", title.lower())
    t = re.sub(r"\s+", "-", t).strip("-")
    return t[:60] or "untitled"


def main() -> int:
    raw = sys.stdin.read()
    text, redactions = redact(raw)
    word_count = len(re.findall(r"\b\w+\b", text))

    warnings: list[str] = []
    if word_count < 200:
        warnings.append(f"source is short ({word_count} words) — confirm with user before proceeding")

    title, sections, has_timestamps = split_sections(text)
    if not title:
        first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "Untitled")
        title = first_line[:80]

    frameworks = detect_frameworks(sections)
    narrative = detect_narrative(sections)
    evidence = extract_evidence(sections)
    references = detect_references(text)

    if not sections and not evidence:
        warnings.append("no headings or numeric evidence detected — source may not be research-like")
    if has_timestamps:
        warnings.append("timestamps detected — attach to slides/mindmap and build deep-links if source is YouTube")
    if references:
        warnings.append(f"{len(references)} external references detected — resolve each with WebSearch before generating artifacts")

    out = {
        "title": title,
        "topic_slug_hint": topic_slug_hint(title),
        "word_count": word_count,
        "has_timestamps": has_timestamps,
        "sections": sections,
        "frameworks": frameworks,
        "narrative": narrative,
        "evidence": evidence,
        "references": references,
        "redactions": redactions,
        "warnings": warnings,
    }
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
