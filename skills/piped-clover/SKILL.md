---
name: piped-clover
description: Turn a pasted research summary (Substack article, YouTube transcript, podcast notes, paper abstract) into a Marp slide deck (.md/.pdf/.html), an editable PowerPoint with native charts (.pptx), and an interactive zoomable mind map (.html) — all saved to research-visuals/{topic}/. Use whenever the user pastes long-form research text and says "summarize research", "turn article into slides", "marp deck from summary", "make a deck from this", "mind map from transcript", "visualize this summary", "research visuals", or "slides + mindmap". Trigger on pasted long-form research content even without an explicit command if the follow-up implies they want a visual artifact.
---

# piped-clover

Converts pasted research text into four linked artifacts: a Marp slide deck (md/pdf/html), an editable PowerPoint deck with native charts, and an interactive HTML mind map. Outputs go to `~/research-visuals/{topic-slug}/`.

## When to use

- User pastes a long-form research summary and wants visuals.
- User asks for any of: "slides", "deck", "mind map", "visualize this", "summarize into a pptx".
- Trigger even without an explicit command if the follow-up to a paste is "make something I can present from this".

## When NOT to use

- General Q&A or conversational requests.
- Code tasks (writing/refactoring code).
- Plain text summaries with no visual artifact requested.
- Text under ~200 words, no headings, no evidence — confirm with user before proceeding with a minimal 3-slide deck.

## Preflight (run once, at the start)

This skill runs in two environments — **Claude Code** (your machine, macOS/Linux) and
**Claude Cowork** (the desktop app, a Linux VM). Both have a shell, Python, `npx`, a web
fetch/search tool, and the built-in `pptx` skill, so the workflow is the same. Quickly
confirm what's available and tell the user what this run can produce:

```bash
bash scripts/preflight.sh
```

It checks `python3`, `node`/`npx` (renderers), and notes whether a web tool is available.
- If `node`/`npx` are missing, the render steps (4, 5) will try `scripts/ensure_node.sh`;
  if that can't install node (e.g. blocked npm egress in a managed Cowork), still produce
  `slides.md` + `mindmap.md` + `deck.pptx` and tell the user the HTML/PDF renders were skipped.
- The `pptx` step (6) works in both environments — `pptx` is a built-in skill in each.

## Workflow

### 0. Capture source + citation (required — do this first)

**Input is the pasted text.** Ask the user to paste the transcript, article, show notes, or
their own notes. If they don't have a transcript handy, point them to
[`references/getting-transcripts.md`](references/getting-transcripts.md) — copy-paste steps for
pulling transcripts from **YouTube** and **Apple Podcasts**. (Automated fetching from a URL is a
future addition; for now the skill works from pasted text.)

Before extracting structure or generating anything, collect the full source details. Every artifact must embed them.

Required fields:

- **Title** — exact title of the content as it appears on the source.
- **Channel / author / publication** — e.g. YouTube channel, Substack author, podcast show name.
- **URL** — permalink to the original content.
- **Published date** — when the source was published (ISO format preferred).
- **Captured date** — today's date.

How to populate:

1. **If the user gives a URL alongside the text**, use your web fetch tool (Claude Code: `WebFetch`; Cowork: the built-in Web Fetch) to auto-fill title, channel/author, and published date.
   - YouTube shortcut (when a shell + internet are available): `curl -s "https://www.youtube.com/oembed?url=<URL>&format=json"` gives title + `author_name`; for the publish date: `curl -s "<video-url>" | grep -oE '"uploadDate":"[^"]*"' | head -1`.
2. **If there's no URL**, ask the user for the title and source (channel/author/publication) so the citation is still accurate. Don't fabricate a URL — leave it blank if there genuinely isn't one. Proceed once you have at least a title + source.

Where the citation appears in each artifact:

- `slides.md` / `deck.pptx` title slide — a small citation block under the meta line (title in quotes, channel, published date, captured date, clickable URL on the pptx).
- `slides.md` / `deck.pptx` closing slide — same citation repeated as a footer.
- `mindmap.md` — a top-level `## 📎 Source` branch with the four fields + URL as a markdown link.

Store the source metadata as a `source` object at the top of `structure.json` so downstream scripts can reuse it:

```json
{
  "source": {
    "title": "…",
    "channel": "…",
    "url": "https://…",
    "published": "YYYY-MM-DD",
    "captured": "YYYY-MM-DD"
  },
  "title": "…",
  "sections": [ … ]
}
```

### 1. Extract structure

Run the parser on the pasted text:

```bash
python3 scripts/extract_structure.py < input.txt > structure.json
```

The script does mechanical parsing (headings, bullets, numeric claims, framework names, timestamps, external references). The model fills semantic gaps afterwards by reading `structure.json` and editing it in place if needed. Keys:

- `title`, `topic_slug_hint`, `has_timestamps`
- `sections[]` — `{heading, bullets, quotes, numbers, start_ts, start_seconds, bullet_ts[]}`
- `frameworks[]` — `{name, parts}`
- `narrative` — `{problem, insight, application}`
- `evidence[]` — `{claim, source_span}`
- `references[]` — `{mention, match, context, search_hint}` (to be resolved in Step 1.5)

**Merge the source block captured in Step 0** into `structure.json` before Step 1.5:

```json
{ "source": { "title": "...", "channel": "...", "url": "...", "published": "...", "captured": "..." }, ... }
```

If the input is too short (<200 words) or contains no headings + no evidence, stop and confirm with the user before continuing.

### 1.5. Resolve timestamps and external references

**Timestamps (YouTube, podcast transcripts):** If `has_timestamps` is true AND the source URL is a YouTube video, every section + bullet that carries a `start_ts` can be linked directly into the video:

- Build `t={seconds}s` deep-links: `https://www.youtube.com/watch?v=XYZ&t=225s` (3:45 → 225s).
- Attach these links to section headings in `slides.md`, to H2s in `mindmap.md`, and to slide meta on bullet slides.
- If the source is not YouTube but still has timestamps (podcast transcript, internal recording), keep the `[HH:MM:SS]` prefix as a visible marker on headings and bullets but don't fabricate a URL.

**External references (best-effort — needs a web tool):** For each entry in `references[]`, use your web search tool (Claude Code: `WebSearch`/`WebFetch`; Cowork: built-in Web Search/Web Fetch) to locate the actual paper / study / report. **If no web tool is available** (e.g. a managed Cowork with web tools disabled), skip resolution: leave each reference as `confidence: "unresolved"` and carry on — the deck still builds. When a web tool *is* available, update each entry in place:

- Add `resolved_url` — permalink to the source (canonical: publisher's page, arXiv, SSRN, HBR.org, bcg.com/publications, etc.).
- Add `citation` — a clean one-line citation: `Author(s) (Year). Title. Publisher.`
- Add `confidence` — `high` (exact title + author match), `medium` (strong topical + org match), `low` (best guess).

If a reference can't be confidently resolved, leave `resolved_url` empty and set `confidence: "unresolved"` — it will still appear in the References slide/branch with a note.

Write the updated `structure.json` back before moving on.

### 2. Pick the visual style

Apply this rubric (full examples in `references/style-rubric.md`):

- **framework-first** if `len(frameworks) >= 2` AND frameworks cover >30% of section headings.
- **narrative-arc** if `narrative.problem`, `narrative.insight`, and `narrative.application` are all non-empty.
- **concept-hierarchy** (default) otherwise.

Record the choice at the top of `slides.md` as `<!-- style: framework-first -->`.

### 3. Emit `slides.md` (Marp)

Slide count: 8–16. Frontmatter:

```yaml
---
marp: true
theme: piped-clover
paginate: true
---
```

Use `---` as slide separators. Title slide gets `<!-- _class: lead -->`. Use custom theme classes on appropriate slides: `.framework`, `.narrative-step`, `.concept-parent`.

Structure per style:

- **framework-first** — title → 1-slide TL;DR → one slide per framework (name + parts + 1-line takeaway) → connections slide → implications → Q&A.
- **narrative-arc** — title → problem → why it matters → key insight → supporting evidence (2–3 slides) → framework/tool → application → takeaway.
- **concept-hierarchy** — title → overview (top 3–5 concepts) → 1 slide per major concept with sub-bullets → relationships slide → synthesis → takeaway.

Keep bullets under 12 words. No walls of text.

**Every deck (all styles) also includes — inserted at the end, before the closing source slide:**

- A **Further reading** slide listing each resolved external reference: one line per reference (`[Citation](resolved_url)` — one-line context). If any references are `unresolved`, list them with `[needs lookup]` so the user can chase them.
- A **Source** slide (closing) with the full citation from Step 0: title in quotes, channel/author, published date, captured date, and the permalink URL.

**Timestamps on section slides:** when `has_timestamps` is true and the source is YouTube, put the link in the slide's H3 meta line: `### 🕐 [12:15](https://youtu.be/XYZ?t=735s)` just under the H1 heading. For non-YouTube sources keep the `🕐 12:15` marker without a link.

### 4. Render Marp to PDF + HTML

```bash
bash scripts/render_marp.sh {out_dir}
```

Uses `npx --yes @marp-team/marp-cli`. On failure, run `scripts/ensure_node.sh` once and retry. If it still fails, leave `slides.md` in place and surface the exact `npx` error with the manual render command for the user to run later.

### 5. Generate the mind map

Write `{out_dir}/mindmap.md` following the markmap structure (template in `assets/markmap-template.md`):

- H1 = topic.
- H2 = 3–6 major section branches (one emoji per H2, chosen semantically).
- Bullets as children, max depth 4, max 6 children per node, ≤12 words each.
- Links `[text](url)` only if the source text had that URL explicitly, OR if produced by timestamp/reference resolution in Step 1.5.

**Always include these two extra H2 branches:**

- `## 📎 Source` — the source citation from Step 0 as 4–5 bullets (title, channel/author, published, captured, `[Watch/Read original](url)`).
- `## 📚 References` — one bullet per resolved external reference: `[Citation text](resolved_url) — one-line context`. Unresolved references appear as plain bullets suffixed with `⚠️ needs lookup`.

**Timestamps:** when `has_timestamps` is true and the source is YouTube, each section's H2 gets a timestamp prefix that links into the video: `## 🧠 [03:42](https://youtu.be/XYZ?t=222s) Why agents are hard`. For non-YouTube sources, use `## 🧠 [03:42] Why agents are hard` (no link).

Then:

```bash
bash scripts/render_markmap.sh {out_dir}
```

### 5.5. Generate "So What — For You" (personalised takeaway — required)

Every deck must close with a takeaway that turns the artifact from a generic summary into a decision tool. If a profile is available, ground it in that; otherwise produce a sharp, source-grounded takeaway anyone could act on.

**Read the profile first, if one exists:**

```bash
cat ~/.claude/profile.md 2>/dev/null || echo "(no profile — produce a generic takeaway)"
```

A profile is a short markdown note on the user's ventures / goals / interests. If `~/.claude/profile.md` exists, **read it before writing this section** — the point is grounding, not guessing. If it doesn't exist, skip straight to producing a generic takeaway focused on the source's most actionable insights.

**Produce a `so_what` object and add it to `structure.json`:**

```json
{
  "so_what": {
    "heading": "So What — For You",
    "relevance": "1–2 sentences on why this topic matters. If a profile exists, connect it to the user's ventures / interests concretely. Otherwise, state who this is most useful for and why.",
    "learnings": [
      "2–4 bullets. Each pulls a specific insight from the source and states why it matters.",
      "Prefer the specific over the generic. 'Base models ship faster than your fine-tune' > 'Avoid fine-tuning.'"
    ],
    "actions": [
      "2–4 bullets. Each starts with a verb. If a profile exists, reference something concrete from it.",
      "This-week actions beat this-quarter actions. Ship > study."
    ],
    "questions": [
      "0–2 optional bullets. Open questions the topic raises that would be worth chasing in a future research cycle."
    ]
  }
}
```

**Quality bar:**

- **Specific over generic** — every bullet should be hard to write without having read the source. If a profile exists, each bullet should also be hard to write without having read it.
- **Name the user's ventures / projects** explicitly when a profile provides them.
- **Action-first verbs** — "Pick", "Audit", "Draft", "Compare", "Decide". Avoid "Consider" and "Explore".
- **No preaching** — state the implication, don't moralise.
- **2–4 bullets per section, not 8** — density beats exhaustiveness.

**Where it appears (all three artifacts):**

- **`slides.md`** — one slide with `<!-- _class: narrative-step -->`, H1 "So What — For You", inserted **after the final content slide and before the Further Reading slide**. Structure: short intro line + **Relevance** sub-heading + **Key learnings** sub-heading + **Actions this week** sub-heading. Use bolded sub-headings, not H2 (keeps the slide on one page).
- **`mindmap.md`** — a `## 💡 So What — For You` branch with three child groups: Relevance · Key learnings · Actions. Insert **between the final content H2 and `## 📎 Source`** (so the mindmap reads: content → so-what → source → references).
- **`deck.pptx`** — a slide with `"type": "so_what"` in `slide_spec.json`. Schema detailed in `references/pptx-handoff-schema.md`. The pptx skill renders it with the narrative-step accent.

**If the topic genuinely has no strong connection to the user** (or no profile exists): still produce the slide, but keep it honest — set `relevance` to something like "Most useful for anyone working on X." and keep `learnings` + `actions` grounded in the source itself. Don't fabricate a personal connection.

### 6. Delegate pptx generation

```bash
python3 scripts/build_pptx_payload.py --structure structure.json --out {out_dir}/_pptx_payload
```

This writes `slide_spec.json` and any needed `charts/slideN.csv`. Charts are only included when `structure.json` has explicit numeric evidence — never fabricate data.

**Review the generated charts before handing off.** The extractor is indiscriminate: it will collect incidental numbers (durations, step counts, dates). Open each `charts/slideN.csv`; if a CSV contains unrelated values or values with mixed meanings, delete that chart entry from `slide_spec.json` and remove the CSV. Keep only charts where rows are comparable.

Schema in `references/pptx-handoff-schema.md`. Then invoke the `pptx` skill via the Skill tool with:

> Build `{out_dir}/deck.pptx` from the slide spec at `{out_dir}/_pptx_payload/slide_spec.json`. Use native PowerPoint charts (not images) for any slide where `type == "chart"`, reading numeric data from the referenced CSV in `_pptx_payload/charts/`.

## Output location

Root: `~/research-visuals/` (override by telling Claude a different folder when you run it).

**In Claude Cowork:** write into a **connected workspace folder** instead — Cowork can only
read/write folders the user has connected. If no folder is connected, ask the user to connect
one (or pick an existing connected folder) and use that as the root, so the artifacts land
somewhere they can open.

If the root doesn't exist, confirm with the user before creating it.

Topic slug: `scripts/slugify.py` turns the extracted title into kebab-case, collision-safe (`-2`…`-9`, then `-YYYYMMDD`).

Final tree per run:

```
{root}/{slug}/
├── slides.md
├── slides.pdf
├── slides.html
├── mindmap.md
├── mindmap.html
├── deck.pptx
├── structure.json         # includes source, sections, references[], so_what
└── _pptx_payload/
    ├── slide_spec.json
    └── charts/
        └── slideN.csv
```

**Every artifact carries a personalised "So What — For You" section** (grounded in `~/.claude/profile.md` if present, otherwise source-grounded). See Step 5.5.

## Safety

Before writing any file, redact common secret patterns (API keys, bearer tokens, `-----BEGIN ... PRIVATE KEY-----` blocks, email/password pairs) from the pasted text. Flag any redactions to the user in your summary.

## Failure modes

- **node/brew missing** — `ensure_node.sh` installs node via brew. If brew is also missing, stop and give the install URL; do not curl-pipe installers.
- **Marp/markmap render fails** — keep the `.md`, skip the rendered output, print the manual command.
- **Slug collision** — `slugify.py` handles.
- **Source too short** — confirm with user before proceeding.

## End-of-run summary

Report back to the user with: the output dir, the 6 file paths, the chosen style, the captured source citation (title + channel + URL), and any warnings (render skipped, secrets redacted, etc.). One or two sentences — the artifacts speak for themselves.
