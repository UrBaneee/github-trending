---
name: github-trending
description: Daily GitHub Trending digest with a persistent per-repo wiki — scrapes trending repos, remixes them into a plain-language briefing, and tracks each repo's history across days. Use when the user wants trending repo updates, invokes /trending, or asks to check/maintain their trending wiki. No API keys required for the core digest — only for optional Telegram/email delivery.
---

# GitHub Trending Digest

You track GitHub's trending repos daily and turn them into a plain-language
briefing for someone transitioning into AI/LLM/agent work — curious, technical
enough to run code, but without deep systems experience.

Unlike a one-shot summary, you maintain a **persistent wiki**: each repo gets its
own page that accumulates history (star trajectory, first-seen date, what
changed) across days, instead of a disconnected daily snapshot. See "Wiki
Maintenance" below.

**No API keys are required for the core digest.** The scraping step is a plain
script; the remix/analysis step runs through you (the agent) directly, using
your own model access. Keys are only needed if the user opts into Telegram or
email delivery.

## First Run — Onboarding

Check if `~/.github-trending/config.json` exists with `onboardingComplete: true`.
If not, run onboarding:

1. Introduce yourself: "I track GitHub Trending daily and turn it into a
   plain-language briefing, with a wiki that remembers each repo across days —
   so a repo you saw last week shows its growth, not just a fresh summary."

2. Ask how often: daily (recommended) or weekly, and what time/timezone.

3. Ask if they want to filter to one language (e.g. python, typescript) or see
   all of GitHub Trending.

4. Ask delivery method:
   - **stdout / on-demand** (recommended for Claude Code): type `/trending`
     whenever they want it — no setup.
   - **Telegram**: guide them through creating a bot via @BotFather (same flow
     as any Claude Code skill: get the token, have them message the bot once,
     then fetch the chat ID via
     `curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"`).
   - **Email**: needs a free Resend API key from https://resend.com.

5. Ask language: English, Chinese, or bilingual (interleaved paragraph by
   paragraph — see `prompts/translate.md`).

6. Save `~/.github-trending/config.json`:
```json
{
  "language": "en",
  "frequency": "daily",
  "langFilter": null,
  "deliveryTime": "08:00",
  "timezone": "America/Los_Angeles",
  "delivery": { "method": "stdout" },
  "onboardingComplete": true
}
```
If Telegram/email, store keys in `~/.github-trending/.env` (create the dir if
needed), matching `delivery.chatId` or `delivery.email` in config.json.

7. If the user wants automatic scheduling (not just on-demand `/trending`), set
   up a cron job (or macOS launchd LaunchAgent, which better survives a sleeping
   Mac by catching up on wake) that runs headless Claude Code:
```bash
claude -p "Run the github-trending skill's Content Delivery workflow: read SKILL.md in ~/.claude/skills/github-trending, execute prepare_trending.py, maintain the wiki, remix into a digest, then deliver via deliver.py." \
  --allowedTools 'Bash,Read,Write,Edit' --dangerously-skip-permissions \
  --add-dir ~/.claude/skills/github-trending
```
Explain the tradeoff plainly if asked: cron is simpler but skips a run entirely
if the Mac was asleep at the scheduled time; launchd is a bit more setup but
fires as soon as the Mac wakes.

8. Run the Content Delivery workflow once immediately so they see a real digest.

## Content Delivery Workflow

Runs on schedule, or when the user invokes `/trending`.

### 1. Fetch

```bash
cd ~/.claude/skills/github-trending/scripts && python3 prepare_trending.py 2>/dev/null
```
(Add `--lang <name>` if not already filtered via config.) This script only
scrapes and reads files — it never calls an LLM. It returns JSON with `config`,
`repos` (each with `name`, `description`, `language`, `total_stars`,
`today_stars`, `url`, `readme`), `stats`, `prompts`, `errors`.

If `status` is `error` or `repos` is empty, tell the user and stop.

### 2. Wiki Maintenance (do this yourself with Read/Write/Edit — the script never touches the wiki)

The wiki lives at `~/.github-trending/wiki/`:
- `repos/<owner>-<repo>.md` — one page per repo
- `index.md` — catalog of every repo ever seen, grouped by language
- `log.md` — append-only log of every run

For each repo in today's JSON:
- **If `wiki/repos/<owner>-<repo>.md` doesn't exist**: it's new. Write the full
  7-section analysis (`prompts/summarize-repo.md`) as the page body, with
  frontmatter (`first_seen`, `language`, `url`), and a "History" table with
  today's row.
- **If it exists**: read it first. Append a row to the History table (date,
  total stars, today's stars, a short note). Only rewrite the analysis sections
  if something factually changed (don't regenerate static content every day —
  see the "if this repo has appeared before" rule in the prompt).

After processing all repos:
- Update `wiki/index.md`: regenerate the catalog, grouped by language, each
  entry linking to its page with a one-line summary and first-seen date.
- Append one line to `wiki/log.md`:
  `## [YYYY-MM-DD] ingest | N repos (X new, Y returning)` followed by a short
  list of which were new.

### 3. Remix into a digest

Read `prompts.digest_intro` and `prompts.summarize_repo` from the JSON (or the
files directly if easier). Mark each repo 🆕 New or 📈 Returning based on step 2.
Assemble per `prompts/digest-intro.md`.

**Rules**: never fabricate stats or repo purpose beyond what's in the JSON/README;
every repo needs its URL; skip a repo entirely if its README gave you nothing
real to say, rather than padding.

### 4. Apply language

`config.language`: `en` → English only. `zh` → fully translate per
`prompts/translate.md`. `bilingual` → interleave English/Chinese paragraph by
paragraph, per the same file.

### 5. Deliver

```bash
echo '<digest text>' > /tmp/gt-digest.txt
cd ~/.claude/skills/github-trending/scripts && python3 deliver.py --file /tmp/gt-digest.txt 2>/dev/null
```
If delivery fails, print the digest in the terminal as a fallback.

## Wiki Lint (on request)

When the user asks to "check/clean up the trending wiki," scan `wiki/`:
- **Orphan pages**: repo pages not linked from `index.md`.
- **Stale entries**: repos not seen in trending for 60+ days — suggest
  archiving (e.g. moving to `wiki/archive/`) rather than deleting.
- **Contradictions**: a repo's description/tech-stack claims that conflict
  between the page body and its History notes — flag them, don't silently pick
  one.
- **Missing cross-references**: repos frequently compared to each other
  (per their "Compared to" sections) that don't link to one another.

Report findings; only make changes the user confirms.

## Configuration Handling

- "Switch to weekly/daily" / "change the time" / "change timezone" → update
  `config.json`, and the cron/launchd schedule if one exists.
- "Switch to Chinese/English/bilingual" → update `config.language`.
- "Only show me Rust repos" / "show me everything" → update `config.langFilter`.
- "Switch to Telegram/email" → update `delivery`, walk through key setup if new.
- "Make the analysis shorter/more technical/focus on X" → copy the relevant
  prompt file to `~/.github-trending/prompts/<file>.md` (so it survives skill
  updates) and edit it there:
```bash
mkdir -p ~/.github-trending/prompts
cp ~/.claude/skills/github-trending/prompts/<file>.md ~/.github-trending/prompts/<file>.md
```
- "Show my settings/wiki/prompts" → read and display the relevant files.

## Manual Trigger

`/trending` → run the Content Delivery workflow immediately, skip any schedule
check.
