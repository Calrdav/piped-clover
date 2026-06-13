#!/usr/bin/env bash
# Ensure node + npx are available (needed for marp-cli and markmap-cli).
# Cross-platform: works on macOS (Claude Code) and Linux (Claude Cowork's VM).
set -euo pipefail

if command -v node >/dev/null 2>&1 && command -v npx >/dev/null 2>&1; then
    exit 0
fi

echo "node/npx not found — attempting install..." >&2

# macOS → Homebrew
if [[ "$(uname -s)" == "Darwin" ]]; then
    if command -v brew >/dev/null 2>&1; then
        brew install node
        exit 0
    fi
    cat >&2 <<'EOF'
Homebrew not found. piped-clover needs node (for marp-cli and markmap-cli).
Install Homebrew from https://brew.sh then re-run, or install Node from https://nodejs.org.
EOF
    exit 1
fi

# Linux (incl. Cowork VM) → try common package managers without sudo prompts first
if command -v apt-get >/dev/null 2>&1; then
    (apt-get install -y nodejs npm || sudo apt-get install -y nodejs npm) && exit 0
fi
if command -v dnf >/dev/null 2>&1; then
    (dnf install -y nodejs npm || sudo dnf install -y nodejs npm) && exit 0
fi
if command -v apk >/dev/null 2>&1; then
    (apk add --no-cache nodejs npm || sudo apk add --no-cache nodejs npm) && exit 0
fi

cat >&2 <<'EOF'
Could not auto-install node. piped-clover needs node + npx for the Marp and
mind-map renderers. Install Node 18+ (https://nodejs.org) and re-run the skill.

In Claude Cowork: node is usually preinstalled in the VM. If this message
appears, your environment may be blocking the npm registry — ask your admin to
allow egress to the npm + PyPI package managers (the default "Trusted" list).
EOF
exit 1
