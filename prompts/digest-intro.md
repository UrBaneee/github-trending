# Digest Assembly Prompt

You are assembling the final daily digest from the individual repo analyses.

## Format

Start with this header (replace [Date] with today's date):

GitHub Trending Digest — [Date]

Then:

## Today's Overview
One paragraph calling out the 2–3 repos most worth a reader's attention today,
and any pattern across today's trending list (e.g. "three of today's five repos
are agent frameworks").

## Repos
List each repo as its own section, in trending order (highest today-star-count
first). For each:

- Header: repo name, total stars, today's star delta — e.g.
  "### 1. owner/repo ⭐ 12,400 (+850 today)"
- A badge noting 🆕 New (first time in the wiki) or 📈 Returning (seen before,
  with the date first seen)
- The 7-section analysis from the repo-analysis prompt
- The repo's URL

## Rules

- Every repo MUST include its GitHub URL. No link = do not include.
- Do NOT fabricate star counts, languages, or descriptions — use only what's in
  the JSON.
- If a repo's README couldn't be fetched, say so plainly instead of guessing at
  what the project does.
- Keep formatting scannable — this is read on a phone screen.
- At the very end, add: "Generated through the github-trending skill."
