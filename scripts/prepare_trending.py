#!/usr/bin/env python3
"""
GitHub Trending — Prepare
==========================
Deterministic data-gathering step, no LLM calls.

Scrapes github.com/trending, fetches each repo's README, loads the user's
config and prompts, and prints a single JSON blob to stdout. The calling
agent's ONLY job is to read this JSON, remix it into a digest, and maintain
the wiki — this script never touches the model.

Usage:
    python3 prepare_trending.py [--lang python]
Output: JSON to stdout
"""

import argparse
import base64
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).parent
LOCAL_PROMPTS_DIR = SCRIPT_DIR.parent / "prompts"

USER_DIR = Path.home() / ".github-trending"
CONFIG_PATH = USER_DIR / "config.json"
USER_PROMPTS_DIR = USER_DIR / "prompts"

PROMPT_FILES = ["summarize-repo.md", "digest-intro.md", "translate.md"]


def fetch_trending(lang: str | None) -> list[dict]:
    url = "https://github.com/trending"
    if lang:
        url += f"/{lang}"

    resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []

    for article in soup.select("article.Box-row"):
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        full_name = h2.get("href", "").strip("/")
        if not full_name:
            continue

        desc_tag = article.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        lang_tag = article.select_one("[itemprop='programmingLanguage']")
        language = lang_tag.get_text(strip=True) if lang_tag else ""

        star_links = article.select("a.Link--muted")
        total_stars = star_links[0].get_text(strip=True).replace(",", "") if star_links else ""

        today_stars_tag = article.select_one("span.d-inline-block.float-sm-right")
        today_stars = ""
        if today_stars_tag:
            today_stars = today_stars_tag.get_text(strip=True).split(" ")[0].replace(",", "")

        repos.append({
            "name": full_name,
            "description": description,
            "language": language,
            "total_stars": total_stars,
            "today_stars": today_stars,
            "url": f"https://github.com/{full_name}",
        })

    return repos


def fetch_readme(repo_name: str) -> str:
    url = f"https://api.github.com/repos/{repo_name}/readme"
    try:
        resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code != 200:
            return ""
        data = resp.json()
        content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
        return content[:3000]
    except Exception:
        return ""


def load_config() -> dict:
    default = {
        "language": "en",
        "frequency": "daily",
        "langFilter": None,
        "delivery": {"method": "stdout"},
    }
    if CONFIG_PATH.exists():
        try:
            return {**default, **json.loads(CONFIG_PATH.read_text())}
        except Exception as err:
            default["_configError"] = str(err)
    return default


def load_prompts() -> tuple[dict, list[str]]:
    """Priority: user custom > local default shipped with the skill."""
    prompts = {}
    errors = []
    for filename in PROMPT_FILES:
        key = filename.replace(".md", "").replace("-", "_")
        user_path = USER_PROMPTS_DIR / filename
        local_path = LOCAL_PROMPTS_DIR / filename

        if user_path.exists():
            prompts[key] = user_path.read_text(encoding="utf-8")
        elif local_path.exists():
            prompts[key] = local_path.read_text(encoding="utf-8")
        else:
            errors.append(f"Could not load prompt: {filename}")
    return prompts, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default=None, help="Filter trending by language, e.g. python")
    args = parser.parse_args()

    errors = []
    config = load_config()
    if config.get("_configError"):
        errors.append(f"Could not read config: {config.pop('_configError')}")

    lang_filter = args.lang or config.get("langFilter")

    try:
        repos = fetch_trending(lang_filter)
    except Exception as err:
        print(json.dumps({"status": "error", "message": str(err)}))
        sys.exit(1)

    if not repos:
        errors.append("No trending repos found (check network connection or GitHub markup changes)")

    for repo in repos:
        repo["readme"] = fetch_readme(repo["name"])

    prompts, prompt_errors = load_prompts()
    errors.extend(prompt_errors)

    output = {
        "status": "ok",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "date": date.today().isoformat(),
        "config": {
            "language": config.get("language", "en"),
            "frequency": config.get("frequency", "daily"),
            "langFilter": lang_filter,
            "delivery": config.get("delivery", {"method": "stdout"}),
        },
        "repos": repos,
        "stats": {
            "repoCount": len(repos),
        },
        "prompts": prompts,
        "errors": errors or None,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
