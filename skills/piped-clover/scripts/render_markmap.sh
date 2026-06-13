#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: render_markmap.sh <out_dir>" >&2
    exit 2
fi

OUT_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$OUT_DIR/mindmap.md" ]]; then
    echo "$OUT_DIR/mindmap.md not found" >&2
    exit 1
fi

render() {
    npx --yes markmap-cli "$OUT_DIR/mindmap.md" \
        --no-open \
        --output "$OUT_DIR/mindmap.html"
}

if ! render 2> "$OUT_DIR/.markmap-render.log"; then
    echo "markmap render failed. Running ensure_node.sh..." >&2
    bash "$SCRIPT_DIR/ensure_node.sh"
    if ! render 2>> "$OUT_DIR/.markmap-render.log"; then
        echo "markmap render failed. See $OUT_DIR/.markmap-render.log" >&2
        echo "Manual render: npx --yes markmap-cli '$OUT_DIR/mindmap.md' --no-open -o '$OUT_DIR/mindmap.html'" >&2
        exit 1
    fi
fi

echo "Rendered: $OUT_DIR/mindmap.html"
