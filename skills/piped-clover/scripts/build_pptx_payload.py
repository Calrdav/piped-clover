#!/usr/bin/env python3
"""Convert structure.json into a pptx payload the anthropic-skills:pptx skill can consume.

Writes:
    {out}/slide_spec.json
    {out}/charts/slideN.csv  (only when numeric evidence exists)

Usage:
    python3 build_pptx_payload.py --structure structure.json --out {out_dir}/_pptx_payload [--style concept-hierarchy]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


def pick_style(structure: dict) -> str:
    frameworks = structure.get("frameworks", [])
    narrative = structure.get("narrative", {})
    sections = structure.get("sections", [])
    section_count = max(len(sections), 1)

    if len(frameworks) >= 2 and (len(frameworks) / section_count) > 0.30:
        return "framework-first"
    if all(narrative.get(k) for k in ("problem", "insight", "application")):
        return "narrative-arc"
    return "concept-hierarchy"


def _youtube_timestamp_link(source_url: str | None, seconds: int | None) -> str | None:
    if not source_url or seconds is None:
        return None
    if "youtube.com" not in source_url and "youtu.be" not in source_url:
        return None
    sep = "&" if "?" in source_url else "?"
    return f"{source_url}{sep}t={int(seconds)}s"


def build_slides(structure: dict, style: str) -> tuple[list[dict], list[tuple[str, list[list]]]]:
    slides: list[dict] = []
    charts: list[tuple[str, list[list]]] = []
    source = structure.get("source") or {}
    source_url = source.get("url")

    def _section_timestamp_meta(sec: dict) -> dict:
        meta: dict[str, Any] = {}
        ts = sec.get("start_ts")
        if ts:
            meta["timestamp"] = ts
            meta["timestamp_seconds"] = sec.get("start_seconds")
            link = _youtube_timestamp_link(source_url, sec.get("start_seconds"))
            if link:
                meta["timestamp_url"] = link
        return meta

    title = structure.get("title", "Untitled")
    title_slide: dict[str, Any] = {"type": "title", "title": title, "subtitle": style.replace("-", " ").title()}
    if source:
        title_slide["source"] = {
            k: source.get(k) for k in ("title", "channel", "url", "published", "captured") if source.get(k)
        }
    slides.append(title_slide)

    if style == "framework-first":
        frameworks = structure["frameworks"]
        slides.append(
            {
                "type": "bullets",
                "title": "TL;DR",
                "bullets": [f"{f['name']} — {len(f['parts'])} components" for f in frameworks[:5]],
            }
        )
        for fw in frameworks[:6]:
            slides.append(
                {
                    "type": "framework",
                    "title": fw["name"],
                    "parts": [{"name": p.split(":")[0][:40], "desc": p[:160]} for p in fw["parts"][:6]],
                }
            )
    elif style == "narrative-arc":
        narrative = structure["narrative"]
        for key, heading in (("problem", "The Problem"), ("insight", "The Insight"), ("application", "Application")):
            if narrative.get(key):
                slides.append(
                    {
                        "type": "bullets",
                        "title": heading,
                        "bullets": _split_into_bullets(narrative[key]),
                    }
                )
    else:  # concept-hierarchy
        for sec in structure.get("sections", [])[:8]:
            bullets = [b for b in sec["bullets"][:5] if b]
            if not bullets:
                continue
            slide: dict[str, Any] = {"type": "bullets", "title": sec["heading"], "bullets": bullets}
            slide.update(_section_timestamp_meta(sec))
            slides.append(slide)

    chart_candidates = _collect_chart_data(structure)
    for i, (chart_title, rows) in enumerate(chart_candidates, start=1):
        csv_path = f"charts/slide{i}.csv"
        charts.append((csv_path, rows))
        slides.append(
            {
                "type": "chart",
                "title": chart_title,
                "chart_type": "bar",
                "data_csv": csv_path,
                "x_label": "Item",
                "y_label": "Value",
            }
        )

    takeaway = _derive_takeaway(structure)
    if takeaway:
        slides.append({"type": "bullets", "title": "Takeaway", "bullets": takeaway})

    so_what = structure.get("so_what") or {}
    if so_what.get("relevance") or so_what.get("learnings") or so_what.get("actions"):
        so_what_slide: dict[str, Any] = {
            "type": "so_what",
            "title": so_what.get("heading") or "So What — For You",
        }
        for key in ("relevance", "learnings", "actions", "questions"):
            value = so_what.get(key)
            if value:
                so_what_slide[key] = value
        slides.append(so_what_slide)

    references = structure.get("references", [])
    resolved = [r for r in references if r.get("resolved_url")]
    if resolved:
        slides.append({
            "type": "references",
            "title": "Further reading",
            "items": [
                {
                    "label": r.get("citation") or r.get("mention", ""),
                    "url": r["resolved_url"],
                    "context": r.get("context", "")[:140],
                }
                for r in resolved
            ],
        })

    if source:
        slides.append({
            "type": "source",
            "title": "Source",
            "source": {
                k: source.get(k) for k in ("title", "channel", "url", "published", "captured") if source.get(k)
            },
        })

    return slides, charts


def _split_into_bullets(text: str, max_bullets: int = 5) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()][:max_bullets]


def _collect_chart_data(structure: dict) -> list[tuple[str, list[list]]]:
    """Group numeric evidence by shared heading into chartable data.

    Only returns groups with 2+ numeric values that share a common unit pattern.
    """
    charts: list[tuple[str, list[list]]] = []
    for sec in structure.get("sections", []):
        numbers = sec.get("numbers", [])
        if len(numbers) < 2:
            continue
        units = {_unit_of(n["value"]) for n in numbers}
        if len(units) > 2:
            continue
        rows = [["label", "value"]]
        for num in numbers[:8]:
            label = _short_label(num["context"], num["value"])
            value = _numeric_part(num["value"])
            if value is None:
                continue
            rows.append([label, value])
        if len(rows) >= 3:
            charts.append((sec["heading"], rows))
    return charts[:3]


def _unit_of(value: str) -> str:
    m = re.search(r"[a-zA-Z%]+$", value.strip())
    return m.group(0).lower() if m else ""


def _numeric_part(value: str) -> float | None:
    m = re.search(r"[\d.,]+", value)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _short_label(context: str, value: str) -> str:
    pos = context.lower().find(value.lower())
    if pos == -1:
        return context[:30]
    snippet = context[max(0, pos - 30) : pos].strip(" ,.-")
    return (snippet or context[:30])[:30]


def _derive_takeaway(structure: dict) -> list[str]:
    narrative = structure.get("narrative", {})
    if narrative.get("application"):
        return _split_into_bullets(narrative["application"], max_bullets=4)
    bullets: list[str] = []
    for sec in structure.get("sections", []):
        if any(kw in sec["heading"].lower() for kw in ("takeaway", "conclusion", "summary")):
            bullets.extend(sec["bullets"][:4])
    return bullets[:4]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--style", default=None)
    args = ap.parse_args()

    structure = json.loads(args.structure.read_text(encoding="utf-8"))
    style = args.style or pick_style(structure)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "charts").mkdir(exist_ok=True)

    slides, charts = build_slides(structure, style)

    for rel_path, rows in charts:
        csv_path = args.out / rel_path
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)

    spec = {
        "title": structure.get("title", "Untitled"),
        "author": "piped-clover",
        "style": style,
        "slides": slides,
    }
    (args.out / "slide_spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}/slide_spec.json ({len(slides)} slides, {len(charts)} charts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
