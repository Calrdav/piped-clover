# Getting a transcript to paste into piped-clover

piped-clover works from **pasted text**. Any of these works: a transcript, a full
article, podcast show notes, a paper abstract, or even your own notes. If you have a
URL but no text yet, grab the transcript with one of the methods below and paste it in.
Include the source **title** and **author/channel** so the citation is accurate — and
keep timestamps if you have them (piped-clover turns YouTube `[mm:ss]` marks into
clickable deep-links).

---

## YouTube

**Desktop browser (fastest):**
1. Open the video.
2. Under the video, click **More (…)** → **Show transcript**. (On some layouts it's in
   the **⋯** menu beside Save, or in the description panel.)
3. A transcript panel opens on the right, with timestamps.
4. To drop the timestamps, click the **⋮** at the top of the panel → **Toggle timestamps**.
   For piped-clover, **keeping** timestamps is better — it enables video deep-links.
5. Click into the panel, select all (Cmd/Ctrl-A), copy, and paste into the chat.

**If "Show transcript" isn't there:** the creator disabled captions. Try:
- Switching captions language in the player, or
- A web search for `"<video title>" transcript`, or
- (Step 2 of piped-clover will automate this with `yt-dlp` — not available yet.)

**Also paste:** the video **title** and **channel name** (shown under the video), and the
URL, so the deck is cited correctly.

---

## Apple Podcasts

Apple added in-app transcripts (iOS 17.4+ / recent macOS). Availability varies by show.

**On Mac:**
1. Open **Podcasts** → the episode.
2. Click the **transcript icon** (a small speech-bubble / quote glyph) near the playback
   controls, or **⋯ → View Transcript**.
3. Scroll through so the full transcript loads.
4. Select the text in the transcript view and copy it.

**On iPhone/iPad:** open the episode → **⋯ → View Transcript**. Selecting the *entire*
transcript can be fiddly on iOS — if copy is limited, use a fallback below.

**Fallbacks (often easier than Apple's copy):**
- Many shows publish a transcript on **their own website or Substack** — check the episode
  page there.
- Podcast platforms like **Spotify**, **Snipd**, or the show's host page often have
  selectable transcripts.
- Web search: `"<episode title>" <show name> transcript`.

**Also paste:** the **episode title** and **show name**, plus the episode URL if you have one.

---

## Anything else

No transcript at all? Paste whatever you have — the article body, the show notes, a
summary, or your own bullet notes. piped-clover needs roughly **200+ words with some
structure** (headings or clear points) to build a useful deck; below that it'll check with
you before making a minimal version.
