#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: render_marp.sh <out_dir>" >&2
    exit 2
fi

OUT_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
THEME="$SKILL_DIR/assets/marp-theme.css"

if [[ ! -f "$OUT_DIR/slides.md" ]]; then
    echo "$OUT_DIR/slides.md not found" >&2
    exit 1
fi

render() {
    npx --yes @marp-team/marp-cli "$OUT_DIR/slides.md" \
        --theme-set "$THEME" \
        --allow-local-files \
        -o "$OUT_DIR/slides.pdf"
    npx --yes @marp-team/marp-cli "$OUT_DIR/slides.md" \
        --theme-set "$THEME" \
        --allow-local-files \
        --html \
        -o "$OUT_DIR/slides.html"
}

if ! render 2> "$OUT_DIR/.marp-render.log"; then
    echo "Marp render failed on first attempt. Running ensure_node.sh..." >&2
    bash "$SCRIPT_DIR/ensure_node.sh"
    if ! render 2>> "$OUT_DIR/.marp-render.log"; then
        echo "Marp render failed. See $OUT_DIR/.marp-render.log" >&2
        echo "Manual render: npx --yes @marp-team/marp-cli '$OUT_DIR/slides.md' --theme-set '$THEME' -o '$OUT_DIR/slides.pdf'" >&2
        exit 1
    fi
fi

echo "Rendered: $OUT_DIR/slides.pdf, $OUT_DIR/slides.html"
