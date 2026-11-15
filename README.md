# GitHub Trending 2.0

A Claude Code skill that helps you **discover GitHub projects and actually learn
them**. It still turns GitHub Trending into a daily plain-language briefing, but
2.0 adds a guided study mode and a persistent personal learning trail—not just a
longer summary.

> **2.0 update:** GitHub Trending started as a discovery digest. It is now a
> project-learning companion. The new study workflow moves from business context
> to system map, one traced code path, AI/framework boundaries, an unprepared
> capability test, author contribution, production readiness, and finally the
> learner's own teach-back.

## Quick Start

```bash
git clone https://github.com/UrBaneee/github-trending.git ~/.claude/skills/github-trending
cd ~/.claude/skills/github-trending/scripts && pip install -r ../requirements.txt
```

Then, in Claude Code, say **"set up github trending"** or invoke `/trending`.
The agent walks you through onboarding conversationally: how often, which
language filter (if any), delivery method (on-demand, Telegram, or email), and
output language (English/Chinese/bilingual).

When a repo catches your attention, say:

```text
study owner/repo
```

or:

```text
continue studying owner/repo
```

**No API key required.** The scraping step (`scripts/prepare_trending.py`) is a
plain script with no LLM calls; the analysis/remix step runs through Claude
Code itself, using whatever model access you already have. Keys are only
needed if you opt into Telegram or email delivery.

## How It Works

### Discovery Mode

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

Each digest now includes a repo-specific **Study hook**—an unanswered question
designed to move you beyond the README.

### Guided Study Mode — new in 2.0

Selecting a repo starts a staged, evidence-backed learning process:

1. **Reality** — who uses it, what happened before it existed, and what changes.
2. **System map** — inputs, transformations, outputs, and consumers.
3. **Trace one path** — follow one real action or result through the code.
4. **Mechanism boundary** — deterministic logic, AI/models, tools, and platform
   capabilities.
5. **Capability boundary** — challenge it with a realistic question the demo did
   not prepare.
6. **Contribution and production** — what the author built versus what frameworks
   provide; what is demo-only versus production-critical.
7. **Teach-back** — explain the project in your own words and extract a reusable
   design lesson.

The workflow inspects repository evidence instead of treating README claims as
implementation proof. It defaults to one stage per conversation turn, so the
user can question and correct their mental model rather than passively reading a
large generated report.

Study progress is saved separately from static repo facts:

```text
~/.github-trending/wiki/repos/<owner>-<repo>.md     # repo facts + trend history
~/.github-trending/wiki/studies/<owner>-<repo>.md  # your learning trail
```

The learning trail remembers:

- questions you actually asked;
- your initial understanding;
- misconceptions corrected by evidence;
- code paths you traced;
- capability-boundary tests;
- your current teach-back and transferable lessons.

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
prompts/study-repo.md       — evidence-backed guided study protocol (2.0)
prompts/learning-trail-template.md — persistent personal study record (2.0)
```

User state (config, wiki, delivery keys) lives outside the repo at
`~/.github-trending/`, so pulling skill updates never clobbers your wiki or
personal prompt customizations.

## Why 2.0?

The first version answered: **"What is trending, and what does this repo do?"**

That is useful for discovery, but summaries alone rarely produce durable
understanding. 2.0 also asks:

- What did users do before this project existed?
- What are the inputs and outputs of each stage?
- Where does an important result come from?
- Which parts are deterministic, AI-driven, or platform-provided?
- What happens on a use case the demo never prepared?
- What did the author actually design and implement?
- Which parts belong to a GitHub demo versus a production system?

The goal is not to make summaries longer. It is to turn curiosity into an
inspectable learning process.

## Maintenance

This project is actively maintained. Version 2.0 expands the original daily
digest into a two-mode workflow while keeping existing discovery, delivery, and
wiki-history behavior compatible.

## Credits

`scripts/deliver.py` (Telegram/email/stdout delivery) is a Python port of the
delivery script from [follow-builders](https://github.com/zarazhangrui/follow-builders)
by Zara Zhang, used under its MIT license. The onboarding/config/scheduling
conventions in `SKILL.md` are also modeled on that project's structure.

## License

MIT — see [LICENSE](LICENSE).
