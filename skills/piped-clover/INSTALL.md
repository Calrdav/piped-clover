# Installing piped-clover

> Two ways to install, depending on which app you use. **Claude Cowork** users (desktop
> app, no terminal) should use the GUI flow; **Claude Code** users use the symlink below.
> The top-level [`README.md`](../../README.md) has both with more context.

## Claude Cowork (desktop app — no terminal)

1. Download/clone the whole `piped-clover` folder to your machine.
2. In the Claude desktop app → **Cowork** → **Customize** → **Skills / Extensions** →
   **+ Add**, and point it at the `skills/piped-clover` folder.
3. **Connect a folder** for outputs (Cowork only writes to folders you connect).
4. Paste a transcript and ask for "a deck and mind map".
5. Managed/enterprise Cowork only: if renders fail, ask your admin to allow egress to the
   **npm** + **PyPI** package registries. You'll still get `.md` + `.pptx` without them.

## Claude Code (terminal)

1. Unzip/clone this folder somewhere you want to keep it (e.g. `~/Claude/Skills/` or `~/skills/`).

2. Symlink it into Claude Code's user skills directory so it gets discovered. From **inside the unzipped `piped-clover` folder**, run:

   ```bash
   mkdir -p ~/.claude/skills
   ln -sfn "$(pwd)" ~/.claude/skills/piped-clover
   ```

3. Confirm:

   ```bash
   ls -la ~/.claude/skills/piped-clover
   ```

   Should show a symlink pointing back to wherever you unzipped the folder.

## First-run dependencies

The skill handles these automatically on first use, but you can pre-install if you want:

```bash
# node + npx (required for Marp and markmap renderers)
brew install node          # macOS. On Linux use your package manager.

# optional: warm the npx cache
npx --yes @marp-team/marp-cli --version
npx --yes markmap-cli --version
```

It also delegates `.pptx` generation to the built-in `pptx` skill, which ships with Claude Code.

## Usage

Paste a research summary into Claude Code and say one of:

- "summarize this into a deck"
- "turn this article into slides and a mind map"
- "marp deck from this"
- "research visuals for this"

Claude Code loads the skill, extracts the structure, picks a visual style, and writes the output artifacts (`slides.md`, `slides.pdf`, `slides.html`, `mindmap.html`, `deck.pptx`, plus a `structure.json` and `_pptx_payload/` intermediate files) to:

```
~/research-visuals/{topic-slug}/
```

(You can change this output root — see "Output location" in `SKILL.md`.)

## Optional: personalised "So What" takeaway

Step 5.5 of the workflow adds a "So What — For You" slide. If a profile file exists at
`~/.claude/profile.md` (a short markdown note on your ventures / goals / interests), the
skill grounds the takeaway in it. If no profile exists, it produces a generic takeaway —
no setup required.

## Updating

Edit files inside the unzipped `piped-clover/` folder directly. The symlink means changes
are picked up with no re-install step.
