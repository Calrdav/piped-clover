# Visual-style rubric

Three styles, picked from the `structure.json` output. Decide once; use that choice for both the Marp deck and the pptx payload (they share the same narrative).

## framework-first

**Pick when:** the source text explicitly names **2 or more** frameworks / models / canvases / loops / pyramids AND they cover **>30% of section headings**.

**Use for:** articles reviewing multiple mental models, "frameworks for X" lists, explainer pieces that explicitly structure around named models.

**Deck shape (10–14 slides):**

1. Title
2. TL;DR — one-line summary of each framework
3. One slide per framework: name, 3–5 components, one-line takeaway
4. Connections slide — how the frameworks relate
5. Implications
6. Source / further reading

### Positive example

Heading list: "Intro", "The OODA loop", "The Cynefin framework", "When to use each", "Decision debt"
→ frameworks = [OODA loop, Cynefin framework], covers 2/5 headings = 40% → **framework-first**.

### Negative example

"5 tips for better meetings" — a list, not a framework. `extract_structure.py` will match "tips" once but not as a framework. Fall through.

## narrative-arc

**Pick when:** the source has a clear problem → insight → application flow AND all three narrative slots (`problem`, `insight`, `application`) are non-empty.

**Use for:** essays, long-form op-eds, product post-mortems, user-research write-ups.

**Deck shape (10–14 slides):**

1. Title
2. The problem
3. Why it matters (evidence)
4. The insight
5. Supporting evidence (2–3 slides)
6. Framework or tool (if any)
7. Application / what to do
8. Takeaway

### Positive example

Section headings include "The problem", "What we learned", "How to apply" → narrative.problem, narrative.insight, narrative.application all populated → **narrative-arc**.

### Negative example

Only `narrative.problem` populated, nothing else → fall through (probably concept-hierarchy).

## concept-hierarchy (default)

**Pick when:** neither framework-first nor narrative-arc qualifies.

**Use for:** dense informational content, study notes, survey papers, reference overviews.

**Deck shape (10–14 slides):**

1. Title
2. Overview — top 3–5 concepts
3. One slide per major concept with sub-bullets
4. Relationships / dependencies slide
5. Synthesis
6. Takeaway

## Always

- Keep slides ≤ 16. Prefer 10–14.
- Bullets ≤ 12 words.
- No walls of text. Prefer 3–5 bullets per content slide.
- Include a final takeaway slide regardless of style.
- Attribute quotes. Include source URL on the last slide if the input had one.
