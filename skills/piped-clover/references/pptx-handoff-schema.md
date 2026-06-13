# pptx handoff schema

The payload piped-clover writes for the `anthropic-skills:pptx` skill to consume.

## File layout

```
{out_dir}/_pptx_payload/
├── slide_spec.json
└── charts/
    ├── slide5.csv
    └── slide7.csv
```

`slide_spec.json` is the single source of truth. Chart CSVs are referenced by relative path from `slide_spec.json`.

## `slide_spec.json` schema

```json
{
  "title": "string — overall deck title",
  "author": "piped-clover",
  "style": "framework-first | narrative-arc | concept-hierarchy",
  "slides": [
    { "type": "title", "title": "...", "subtitle": "...",
      "source": { "title": "...", "channel": "...", "url": "...", "published": "...", "captured": "..." } },

    { "type": "bullets", "title": "...", "bullets": ["...", "..."],
      "timestamp": "12:15", "timestamp_seconds": 735, "timestamp_url": "https://youtu.be/ID?t=735s" },

    { "type": "framework", "title": "...",
      "parts": [{ "name": "...", "desc": "..." }] },

    { "type": "quote", "text": "...", "attribution": "..." },

    { "type": "chart", "title": "...",
      "chart_type": "bar | line | pie",
      "data_csv": "charts/slide5.csv",
      "x_label": "...", "y_label": "..." },

    { "type": "so_what", "title": "So What — For You",
      "relevance": "1–2 sentences tying the topic to current ventures / context.",
      "learnings": ["bullet", "bullet"],
      "actions": ["verb-first bullet", "verb-first bullet"],
      "questions": ["optional open question"] },

    { "type": "references", "title": "Further reading",
      "items": [
        { "label": "Author (Year). Title. Publisher.",
          "url": "https://...",
          "context": "one-line snippet" }
      ] },

    { "type": "source", "title": "Source",
      "source": { "title": "...", "channel": "...", "url": "...", "published": "...", "captured": "..." } }
  ]
}
```

## Slide type: `so_what`

The personalised takeaway slide. Always present (generated in Step 5.5 of the skill). The pptx consumer should render:

- Slide title = `title` (default "So What — For You").
- Styled with the narrative-step accent (green left rule, slight inset) to distinguish it from content slides.
- Body structure:
  - A bolded sub-heading **"Relevance"** followed by the `relevance` string as a paragraph.
  - A bolded sub-heading **"Key learnings"** followed by `learnings[]` as a bulleted list.
  - A bolded sub-heading **"Actions this week"** followed by `actions[]` as a bulleted list.
  - If `questions[]` is non-empty, a final sub-heading **"Open questions"** with those bullets at 70% opacity.
- Target 8–12 bullets total across the slide; split to two slides if more.

This slide sits **after all content slides and before the Further reading slide**.

## Slide type: `references`

A closing "Further reading" slide. The pptx consumer should render:

- Slide title = the `title` field.
- For each `items[i]`: one bullet line in the format `{label}` as the visible text, styled as a hyperlink pointing at `items[i].url`. Below it, a smaller-font secondary line with `items[i].context` (can be shown in 60–70% opacity). Max 8 items per slide; split to two slides if more.

## Slide type: `source`

The closing source/citation slide. The pptx consumer should render:

- Slide title = "Source".
- A stacked block of 4–5 lines:
  - `"{source.title}"` in italic.
  - `{source.channel}` on the next line, regular weight.
  - `Published: {source.published}` · `Captured: {source.captured}` on one line.
  - The URL rendered as a clickable hyperlink on its own line.

## Timestamp metadata on any slide

Any slide may carry `timestamp`, `timestamp_seconds`, and `timestamp_url` — these originate from a YouTube/podcast source. The pptx consumer should render the timestamp as a small meta-line under the slide title, styled as `🕐 {timestamp}`, and make it a hyperlink to `timestamp_url` when present.

## Chart CSV format

First row is header. Two-column CSVs for bar/line/pie:

```csv
label,value
Q1 2024,32
Q2 2024,45
Q3 2024,48
Q4 2024,51
```

Multi-series charts can extend:

```csv
label,series_a,series_b
Jan,10,20
Feb,14,18
```

## Rules for the consumer (pptx skill)

1. Use **native PowerPoint charts** for `type == "chart"` — not images. The user must be able to right-click → "Edit Data".
2. Read `data_csv` relative to `_pptx_payload/`.
3. Preserve slide order from `slides[]`.
4. Treat `style` as a hint for visual tone only (accent color, layout density). Don't reorder slides based on it.
5. Use the deck title as both the file title and the title-slide headline if no `subtitle` is present.

## Rules piped-clover enforces before writing

- **Never fabricate numeric data.** Charts only appear for numeric claims that came from the source text (tracked via `evidence[].source_span` in `structure.json`).
- **Chart per section, max 3 per deck.** Keeps the deck focused.
- **Redact secrets** in any text that goes into `slide_spec.json`.
