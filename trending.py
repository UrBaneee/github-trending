"""
GitHub Trending 每日总结工具
抓取 GitHub trending 页面，调用 LLM 生成中文总结，输出 Markdown 文件。

用法:
    python trending.py --provider claude
    python trending.py --provider openai
    python trending.py --provider claude --lang python
"""

import argparse
import base64
import os
import sys
from datetime import date
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 加载 .env 文件中的 API key
load_dotenv()

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"


def fetch_trending(lang: str | None = None) -> list[dict]:
    """抓取 GitHub trending 页面，返回项目列表。"""
    url = "https://github.com/trending"
    if lang:
        url += f"/{lang}"

    print(f"正在抓取 {url} ...")
    resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []

    for article in soup.select("article.Box-row"):
        # 项目名称 (owner/repo)
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        full_name = h2.get("href", "").strip("/")
        if not full_name:
            continue

        # 描述
        desc_tag = article.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # 语言
        lang_tag = article.select_one("[itemprop='programmingLanguage']")
        language = lang_tag.get_text(strip=True) if lang_tag else ""

        # 总 star 数
        star_links = article.select("a.Link--muted")
        total_stars = ""
        if star_links:
            total_stars = star_links[0].get_text(strip=True).replace(",", "")

        # 今日 star 数
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

    print(f"共找到 {len(repos)} 个 trending 项目")
    return repos


def fetch_readme(repo_name: str) -> str:
    """通过 GitHub API 获取项目的 README 内容（截取前 3000 字符）。"""
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


def build_prompt(repos: list[dict]) -> str:
    """构造发给 LLM 的 prompt。"""
    today = date.today().isoformat()

    repo_sections = []
    for i, repo in enumerate(repos, 1):
        section = f"""
### 项目 {i}: {repo['name']}
- URL: {repo['url']}
- 描述: {repo['description']}
- 语言: {repo['language']}
- 总 Star: {repo['total_stars']}
- 今日 Star: +{repo['today_stars']}
- README 摘要:
{repo.get('readme', '（无法获取）')}
"""
        repo_sections.append(section)

    prompt = f"""你是一个技术分析专家，正在为一个没有编程和架构经验、正在转行 AI/LLM/Agent 方向的读者做每日技术简报。
请对以下 {today} 的 GitHub Trending 项目进行中文总结分析。

请用通俗易懂的语言，避免太多术语，必要时用类比解释技术概念。

对每个项目，请输出以下 7 个模块：
1. **一句话定位**: 用一句大白话说清楚这个项目是干什么的，比如"开源版 Perplexity，AI 搜索引擎"
2. **它解决了什么痛点**（不少于50字）：为什么有人需要这个项目？之前没有它的时候，人们遇到什么困难？
3. **核心技术原理**（不少于50字）：用大白话解释它的技术原理，尽量用类比，让没有技术背景的人也能理解。比如"就像给 AI 配了一个搜索引擎，先查资料再回答问题"
4. **技术栈**: 列出它用了哪些主要的编程语言、框架和工具，每个简单注释一下是干嘛的
5. **同类对比**: 和市面上哪些项目类似？它们之间的核心区别是什么？用表格或简短对比说明
6. **学习价值**: 对一个正在转行 AI 方向的人来说，这个项目能帮你学到什么？值得深入研究还是了解即可？
7. **上手难度**: 评估一个新手能不能把这个项目跑起来玩，需要什么前置知识

请在开头先写一段"今日概览"，总结今天 trending 的整体趋势和值得重点关注的项目。

请严格使用以下 Markdown 格式输出：

# GitHub Trending 每日总结 - {today}

## 今日概览
（总结段落，指出今天最值得关注的 2-3 个项目）

---

### 1. 项目名 ⭐ 总star数 (+今日star)
**语言**: xxx

**一句话定位**: xxx

**解决的痛点**: （不少于50字）

**核心技术原理**: （不少于50字，用大白话解释）

**技术栈**:
- 语言/框架 — 用途说明
- ...

**同类对比**:
| 项目 | 区别 |
|---|---|
| xxx | xxx |

**学习价值**: （说明对 AI 转行者的价值）

**上手难度**: ⭐⭐⭐ （简要说明）

---

以下是今天的 trending 项目信息：
{"".join(repo_sections)}
"""
    return prompt


def call_claude(prompt: str) -> str:
    """调用 Claude API 生成总结。"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("错误: 请在 .env 文件中设置 ANTHROPIC_API_KEY")
        sys.exit(1)

    from anthropic import Anthropic

    print("正在调用 Claude API 生成总结...")
    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_openai(prompt: str) -> str:
    """调用 OpenAI API 生成总结。"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("错误: 请在 .env 文件中设置 OPENAI_API_KEY")
        sys.exit(1)

    from openai import OpenAI

    print("正在调用 OpenAI API 生成总结...")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(description="GitHub Trending 每日总结工具")
    parser.add_argument(
        "--provider",
        choices=["claude", "openai"],
        required=True,
        help="选择 LLM 提供商: claude 或 openai",
    )
    parser.add_argument(
        "--lang",
        default=None,
        help="只看某个编程语言的 trending，比如 python、typescript",
    )
    args = parser.parse_args()

    # 第一步：抓取 trending
    repos = fetch_trending(args.lang)
    if not repos:
        print("没有找到任何 trending 项目，请检查网络连接。")
        sys.exit(1)

    # 第二步：获取每个项目的 README
    print("正在获取各项目的 README...")
    for i, repo in enumerate(repos):
        print(f"  [{i + 1}/{len(repos)}] {repo['name']}")
        repo["readme"] = fetch_readme(repo["name"])

    # 第三步：调用 LLM
    prompt = build_prompt(repos)

    if args.provider == "claude":
        result = call_claude(prompt)
    else:
        result = call_openai(prompt)

    # 第四步：写入文件
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    output_file = OUTPUT_DIR / f"{today}.md"
    output_file.write_text(result, encoding="utf-8")

    print(f"\n总结已保存到: {output_file}")
    print("完成！")


if __name__ == "__main__":
    main()
