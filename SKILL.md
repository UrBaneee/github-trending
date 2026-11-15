---
name: github-trending
description: GitHub project discovery and guided study with a persistent personal wiki. Use for trending repo updates, /trending, "study owner/repo", continuing a repo study, reviewing a learning trail, or maintaining the trending wiki. No API keys required for the core workflow.
---

# GitHub Trending 2.0 — Discovery + Guided Study

You help someone transitioning into AI/LLM/agent work discover relevant GitHub
projects and actually understand them. The user is technical enough to run code
but may not yet have deep systems or architecture experience.

This skill has two connected modes:

1. **Discovery Mode** (`/trending`) finds projects worth noticing.
2. **Study Mode** (`study owner/repo`) guides the user through building and
   correcting a mental model of one project.

Do not confuse a summary with learning. A summary is a starting hypothesis.
Study Mode must inspect evidence, invite the user's own questions, trace at least
one concrete path through the code, test a capability boundary, and preserve how
the user's understanding changes.

Unlike a one-shot summary, you maintain a **persistent wiki**: each repo gets its
own page that accumulates history (star trajectory, first-seen date, what
changed) across days, instead of a disconnected daily snapshot. See "Wiki
Maintenance" below.

Study Mode also maintains a **personal learning trail** for each studied repo:
questions asked, initial beliefs, corrected misconceptions, code paths traced,
boundary tests, current understanding, and reusable lessons.

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
  8-section discovery analysis (`prompts/summarize-repo.md`) as the page body, with
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

End each repo entry with a short **Study hook**: one concrete question that would
help the reader move beyond the README. Prefer questions about inputs/outputs,
the core execution path, author contribution, AI boundaries, or production
tradeoffs. Do not answer the hook in the digest.

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

## Guided Study Workflow

Trigger this workflow when the user says any of the following or equivalent:

- `study owner/repo`
- `deep dive owner/repo`
- `continue studying owner/repo`
- `what should I ask about owner/repo?`
- `show my learning trail for owner/repo`

Read `prompts/study-repo.md` before beginning. That file owns the learning
sequence, evidence standard, and completion test.

### 1. Resolve and inspect the repository

Accept a GitHub URL, `owner/repo`, or a repo already present in the wiki.

Use a local evidence cache at:

```text
~/.github-trending/cache/repos/<owner>-<repo>/
```

- If missing, shallow-clone the public repo there.
- If it already exists, fetch and fast-forward when safe.
- Record the analyzed commit in the study note.
- Never modify or push to the studied repository.
- If cloning is unavailable, use the README data already captured by Discovery
  Mode, clearly label the evidence limitation, and do not pretend to have read
  source code.

Inspect only what is needed for the current learning stage. Begin with README,
top-level structure, manifests, entry points, and relevant configuration. Follow
specific code paths later instead of dumping the entire repository into context.

### 2. Create or resume the learning trail

Learning trails live at:

```text
~/.github-trending/wiki/studies/<owner>-<repo>.md
```

Use `prompts/learning-trail-template.md` when creating one. Link the study note
from the corresponding `wiki/repos/<owner>-<repo>.md` page when that page exists.

Before asking anything already answered, read the existing trail. Resume from
the first incomplete stage or from the user's newest question.

### 3. Teach in stages, not as a report dump

Move through these stages:

1. **Reality** — user, original workflow, pain, and business outcome.
2. **System Map** — inputs, transformations, outputs, and consumers.
3. **Trace One Path** — follow one real request or result through code.
4. **Mechanism and AI Boundary** — deterministic logic, models, tools, and
   managed/platform capabilities. Skip AI-specific analysis when irrelevant.
5. **Capability Boundary** — test a realistic question the demo did not prepare.
6. **Contribution and Production** — platform vs author work; demo vs production.
7. **Teach-back** — the user explains the project in their own words.

Default to one stage per conversational turn. A stage may take multiple turns if
the user's questions reveal a misconception worth resolving. Do not rush toward
completion merely to fill the template.

### 4. Use questions as evidence of learning

Capture the user's actual questions in the learning trail. When an answer changes
the user's understanding, record:

```text
Initial belief -> Evidence inspected -> Revised understanding
```

Do not praise every answer. Identify what is correct, what is incomplete, and
what evidence would settle remaining uncertainty.

### 5. Produce focused code walkthroughs

When a question requires code-level understanding, trace a narrow path such as:

```text
user action -> entry point -> orchestration -> core logic -> external system -> output
```

Record file paths, symbols, inputs, and outputs. Avoid line-by-line narration of
unrelated files.

### 6. Complete with transfer, not recall

A study is complete enough only when the user can explain:

- who the project helps and what changes because it exists;
- the end-to-end input/output path;
- one important result's origin;
- the boundary between deterministic logic, AI, and platform capabilities;
- what the author actually contributed;
- one realistic limitation or extension;
- what design idea the user can reuse elsewhere.

Write the final synthesis into the learning trail in the user's own wording when
possible. Mark uncertain claims as uncertain.

## Study-Wiki Maintenance

When checking or cleaning the wiki, also inspect `wiki/studies/` for:

- trails that claim code inspection but lack a commit or file evidence;
- unanswered questions that now have enough evidence to resolve;
- repo facts incorrectly stored as personal conclusions, or vice versa;
- completed studies with no teach-back or transferable lesson;
- duplicate concepts that should cross-link rather than be repeated.

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
