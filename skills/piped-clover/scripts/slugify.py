#!/usr/bin/env python3
"""Slugify a topic into a collision-safe kebab-case directory name.

Usage:
    python3 slugify.py "My Topic Title" /path/to/parent

Prints the slug (not the full path) to stdout. If {parent}/{slug} already
exists, appends -2, -3, ..., -9; then -YYYYMMDD as a last resort.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:60] or "untitled"


def collision_safe(parent: Path, slug: str) -> str:
    if not (parent / slug).exists():
        return slug
    for i in range(2, 10):
        candidate = f"{slug}-{i}"
        if not (parent / candidate).exists():
            return candidate
    return f"{slug}-{date.today().strftime('%Y%m%d')}"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: slugify.py <topic> <parent_dir>", file=sys.stderr)
        return 2
    topic, parent_str = sys.argv[1], sys.argv[2]
    parent = Path(parent_str).expanduser()
    print(collision_safe(parent, slugify(topic)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
