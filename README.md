# GitHub Trending Digest

A Claude Code skill that turns GitHub Trending into a daily plain-language
briefing — with a persistent wiki so each repo accumulates history (star
growth, first-seen date) across days instead of a disconnected daily snapshot.

## Quick Start

```bash
git clone https://github.com/UrBaneee/github-trending.git ~/.claude/skills/github-trending
cd ~/.claude/skills/github-trending/scripts && pip install -r ../requirements.txt
```

Then, in Claude Code, say **"set up github trending"** or invoke `/trending`.
The agent walks you through onboarding conversationally: how often, which
language filter (if any), delivery method (on-demand, Telegram, or email), and
output language (English/Chinese/bilingual).

**No API key required.** The scraping step (`scripts/prepare_trending.py`) is a
plain script with no LLM calls; the analysis/remix step runs through Claude
Code itself, using whatever model access you already have. Keys are only
needed if you opt into Telegram or email delivery.

## How It Works

1. `scripts/prepare_trending.py` scrapes `github.com/trending` (optionally
   filtered by language) and each repo's README, and prints a JSON blob — no
   model calls, fully deterministic.
2. Claude Code reads the JSON, checks each repo against
   `~/.github-trending/wiki/repos/<owner>-<repo>.md` — creating a new page for
   first-time repos, or updating the existing one (appending to its star
   history, revising analysis only if something actually changed).
3. It assembles a digest, marking each repo 🆕 New or 📈 Returning, following
   the style rules in `prompts/`.
4. `scripts/deliver.py` sends the digest to stdout, Telegram, or email per your
   config.

See `SKILL.md` for the full workflow the agent follows, including the wiki
lint operation ("clean up my trending wiki") and how to customize the analysis
style by editing `prompts/*.md`.

## Structure

```
SKILL.md                    — agent instructions (onboarding, workflow, wiki rules)
scripts/prepare_trending.py — scrape + README fetch, JSON out, no LLM calls
scripts/deliver.py          — stdout / Telegram / email delivery
prompts/summarize-repo.md   — per-repo analysis style (editable, plain English)
prompts/digest-intro.md     — overall digest assembly rules
prompts/translate.md        — bilingual/Chinese translation rules
```

User state (config, wiki, delivery keys) lives outside the repo at
`~/.github-trending/`, so pulling skill updates never clobbers your wiki or
personal prompt customizations.
