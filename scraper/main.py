"""
LinkedIn job post detector — runs once per invocation (called by GitHub Actions hourly).
Reads credentials from environment variables:
  LI_AT               — LinkedIn li_at session cookie
  TELEGRAM_BOT_TOKEN  — Telegram bot token
  TELEGRAM_CHAT_ID    — Telegram chat / channel ID
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

from scraper.linkedin import LinkedInSearcher
from scraper.login import get_li_at
from scraper.telegram import notify_new_posts
from scraper import store, scorer

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")
JOBS_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "jobs.json")


def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jobs_json(all_posts: list[dict], new_posts: list[dict], config: dict) -> None:
    top_n = config.get("top_results_count", 5)
    ranked = scorer.rank(all_posts, config)

    for post in ranked:
        post["is_new"] = post["id"] in {p["id"] for p in new_posts}

    payload = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "query": config["search_query"],
        "stats": {
            "total": len(ranked),
            "new_this_run": len(new_posts),
            "new_today": store.count_today(ranked),
        },
        "top_results": ranked[:top_n],
        "all_results": ranked,
    }

    os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(ranked)} posts to docs/jobs.json")


def main():
    li_at = os.environ.get("LI_AT", "").strip()
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    # If li_at not given, try email/password login
    if not li_at:
        email = os.environ.get("LI_EMAIL", "").strip()
        password = os.environ.get("LI_PASSWORD", "").strip()
        if email and password:
            print("li_at not set — logging in with email/password...")
            try:
                li_at = get_li_at(email, password)
                print("Login successful, li_at acquired")
            except RuntimeError as e:
                print(f"ERROR: {e}")
                sys.exit(1)
        else:
            print("ERROR: Set LI_AT, or both LI_EMAIL and LI_PASSWORD")
            sys.exit(1)

    if not tg_token or not tg_chat:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        sys.exit(1)

    config = load_config()
    query = config["search_query"]

    print(f"Searching LinkedIn for: {query}")
    searcher = LinkedInSearcher(li_at)
    posts = searcher.search_content(query, count=config.get("max_results", 25))

    if not posts:
        print("No posts returned — check li_at cookie or try again later")
        save_jobs_json([], [], config)
        return

    seen = store.load_seen()
    new_posts = store.filter_new(posts, seen)

    print(f"Total: {len(posts)} | New: {len(new_posts)}")

    if new_posts:
        sent = notify_new_posts(tg_token, tg_chat, new_posts)
        print(f"Telegram: sent {sent}/{len(new_posts)} notifications")

    seen = store.mark_seen(posts, seen)
    store.save_seen(seen)
    save_jobs_json(posts, new_posts, config)


if __name__ == "__main__":
    main()
