# 🍀 piped-clover

Paste a research transcript or article and get back three linked artifacts:

- a **Marp slide deck** (`slides.md` / `.pdf` / `.html`),
- an **editable PowerPoint** with native charts (`deck.pptx`),
- an **interactive zoomable mind map** (`mindmap.html`).

Every output carries the original **source citation** and a personalised **"So What — For
You"** takeaway.

**▶ [See how it works + download](https://calrdav.github.io/piped-clover/)** — a visual walkthrough.

It runs the same in **Claude Code** and **Claude Cowork** (the desktop app) — no extra
services, no API keys. The model you're already talking to does the thinking; the skill does
the fetching-of-shape and rendering.

> **Input today:** you paste the text. Don't have a transcript? See
> [`skills/piped-clover/references/getting-transcripts.md`](skills/piped-clover/references/getting-transcripts.md)
> for copy-paste steps to pull one from **YouTube** or **Apple Podcasts**.
> *(Automated URL fetching is a planned next step.)*

---

## Install

### Option A — Claude Cowork (desktop app, no terminal needed)

For people who **don't** have Claude Code. Cowork runs a full Linux VM with Python + Node +
a built-in PowerPoint skill, so everything works.

1. Download this folder (or `git clone` it) to your machine.
2. In the Claude desktop app, open **Cowork**.
3. **Customize** (top of the sidebar) → **Skills / Extensions** → **Add** (the **+**), and
   point it at this `piped-clover` folder. It installs as a user extension.
4. **Connect a folder** where outputs should be saved (Cowork can only write to folders you
   connect) — e.g. a `research-visuals` folder in your Documents.
5. Start a chat, paste a transcript, and say *"make a deck and mind map from this."*

**One network note:** the slide/mind-map renderers fetch small Node packages from npm the
first time. Cowork allows npm + PyPI by default. On a **managed/enterprise** Cowork, an admin
may need to allow egress to the **npm** and **PyPI** package registries. If renders are
blocked, you still get `slides.md`, `mindmap.md`, and `deck.pptx` — only the rendered
HTML/PDF are skipped.

### Option B — Claude Code (terminal)

```bash
git clone https://github.com/Calrdav/piped-clover.git
cd piped-clover
mkdir -p ~/.claude/skills
ln -sfn "$(pwd)/skills/piped-clover" ~/.claude/skills/piped-clover
```

First run installs Node (for the renderers) automatically if it's missing. Or pre-install:
`brew install node` (macOS) / your package manager (Linux). Outputs go to
`~/research-visuals/{topic}/`.

---

## What's in here

```
piped-clover/
├── .claude-plugin/plugin.json        plugin manifest
├── skills/piped-clover/
│   ├── SKILL.md                      the workflow Claude follows
│   ├── INSTALL.md                    detailed setup notes
│   ├── scripts/                      parsers + renderers + preflight (Python / bash)
│   ├── assets/                       Marp theme, mind-map template
│   ├── references/                   style rubric, pptx schema, getting-transcripts.md
│   └── examples/                     a sample input you can paste to try it
└── README.md                         this file
```

## How it works (30-second version)

1. You paste the text (+ title / source).
2. A Python parser pulls out the structure (headings, bullets, numbers, frameworks,
   timestamps) — deterministic, no guessing.
3. Claude picks a visual style, writes the slides + mind map, and adds a grounded "So What"
   takeaway.
4. Marp + markmap render the deck and the interactive map; the built-in **pptx** skill builds
   the PowerPoint (native charts only where the source has real numbers).

## Requirements

- **Claude Code** or **Claude Cowork**.
- **Python 3** (preinstalled in both).
- **Node 18+** for the renderers (auto-installed in Claude Code; preinstalled in Cowork's VM).
- A web fetch/search tool is used *opportunistically* to resolve cited references — if it's
  unavailable, that step is skipped and the deck still builds.

## Privacy

No personal data is baked in. The "So What — For You" step reads an **optional**
`~/.claude/profile.md` if one exists (a short note on your work/goals) to tailor the takeaway;
with no profile it produces a generic, source-grounded takeaway. Before writing any file the
skill redacts common secret patterns from the pasted text.
