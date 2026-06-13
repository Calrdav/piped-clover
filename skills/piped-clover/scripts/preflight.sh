#!/usr/bin/env bash
# Report what this environment can produce, so the skill can set expectations
# up front. Non-fatal: always exits 0 and just prints a status table.
set -uo pipefail

ok="yes"; no="no"

have() { command -v "$1" >/dev/null 2>&1 && echo "$ok" || echo "$no"; }

echo "piped-clover preflight"
echo "  os         : $(uname -s)"
echo "  python3    : $(have python3)   (required — mechanical parsing)"
echo "  node       : $(have node)"
echo "  npx        : $(have npx)   (renders slides.pdf/.html + mindmap.html)"
echo

if [[ "$(have npx)" == "$no" ]]; then
  cat <<'EOF'
  → node/npx missing. The skill will try scripts/ensure_node.sh during render.
    If that can't install node (e.g. blocked npm egress in a managed Cowork),
    you will still get: slides.md, mindmap.md, and deck.pptx — only the rendered
    HTML/PDF will be skipped. Tell the user that before you start.
EOF
else
  echo "  → renderers available: full output (slides.md/.pdf/.html, mindmap.html, deck.pptx)."
fi

cat <<'EOF'

  Web reference-resolution (Step 1.5) and the pptx step (Step 6) use your
  assistant's own tools (web fetch/search; the built-in pptx skill), which
  this script can't probe — they exist in both Claude Code and Cowork. If a
  managed Cowork has web tools disabled, Step 1.5 is skipped gracefully.
EOF
exit 0
