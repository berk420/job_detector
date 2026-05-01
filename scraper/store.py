import json
import os
from datetime import datetime, timezone

SEEN_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "seen_jobs.json")


def load_seen() -> set[str]:
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen(seen: set[str]) -> None:
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)


def filter_new(posts: list[dict], seen: set[str]) -> list[dict]:
    return [p for p in posts if p["id"] not in seen]


def mark_seen(posts: list[dict], seen: set[str]) -> set[str]:
    return seen | {p["id"] for p in posts}


def count_today(posts: list[dict]) -> int:
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp()
    return sum(1 for p in posts if p.get("timestamp", 0) >= today_start)
