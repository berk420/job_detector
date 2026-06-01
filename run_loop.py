"""
Continuous LinkedIn monitor — keeps Chrome open and checks every N minutes.
Run this directly on the server: python run_loop.py
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

from scraper.browser import LinkedInBrowser
from scraper.telegram import send_message, format_post
from scraper import store

CHECK_INTERVAL = 15 * 60  # seconds between checks

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT   = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
LI_EMAIL        = os.environ.get("LI_EMAIL", "").strip()
LI_PASSWORD     = os.environ.get("LI_PASSWORD", "").strip()


def validate_env():
    missing = []
    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT:
        missing.append("TELEGRAM_CHAT_ID")
    if not LI_EMAIL:
        missing.append("LI_EMAIL")
    if not LI_PASSWORD:
        missing.append("LI_PASSWORD")
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)


def normalize_posts(raw: list[dict]) -> list[dict]:
    posts = []
    for r in raw:
        text = r.get("text", "")
        posts.append({
            "id": r.get("id", ""),
            "text": text[:350] + "…" if len(text) > 350 else text,
            "full_text": text,
            "author_name": r.get("authorName", ""),
            "author_title": r.get("authorTitle", ""),
            "url": r.get("url", ""),
            "timestamp": 0,
            "likes": 0,
            "comments": 0,
        })
    return [p for p in posts if p["id"] and p["text"]]


def main():
    validate_env()

    print("=" * 50)
    print("  LinkedIn Job Monitor — Browser Mode")
    print("=" * 50)

    headless = os.environ.get("HEADLESS", "true").lower() != "false"
    browser = LinkedInBrowser(headless=headless)
    browser.start()

    # Login (skip if saved cookies are still valid)
    if not browser.is_logged_in():
        print("Not logged in — attempting login...")
        ok = browser.login(LI_EMAIL, LI_PASSWORD)
        if not ok:
            print("Login failed. Exiting.")
            browser.close()
            sys.exit(1)
    else:
        print("Already logged in via saved session")

    print(f"\nMonitor started. Checking every {CHECK_INTERVAL // 60} minutes.")
    print("Keep this window open. Press Ctrl+C to stop.\n")

    while True:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print(f"[{now}] Checking LinkedIn...")

        try:
            raw_posts = browser.fetch_posts()
            posts = normalize_posts(raw_posts)
        except Exception as e:
            print(f"  Fetch error: {e} — will retry next cycle")
            time.sleep(CHECK_INTERVAL)
            continue

        seen = store.load_seen()
        new_posts = store.filter_new(posts, seen)

        if new_posts:
            print(f"  {len(new_posts)} new post(s) — sending to Telegram...")
            sent = 0
            for post in new_posts:
                if send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT, format_post(post)):
                    sent += 1
            print(f"  Sent {sent}/{len(new_posts)} notifications")
        else:
            print(f"  No new posts (total on page: {len(posts)})")

        seen = store.mark_seen(posts, seen)
        store.save_seen(seen)

        print(f"  Next check in {CHECK_INTERVAL // 60} minutes...\n")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
