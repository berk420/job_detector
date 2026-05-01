import time
import re

HIRING_KEYWORDS = [
    "#hiring", "işe alım", "iş ilanı", "başvuru", "ilan",
    "software", "yazılım", "developer", "geliştirici",
    "engineer", "mühendis", "ankara", "remote", "hybrid",
    "python", "java", "javascript", "react", "backend", "frontend",
    "full-stack", "fullstack", "devops", "cloud",
]

STRONG_SIGNALS = ["#hiring", "işe alım", "iş ilanı", "open position", "arıyoruz"]


def score(post: dict, config: dict) -> float:
    weights = config.get("score_weights", {
        "keyword_match": 40,
        "recency": 35,
        "engagement": 25,
    })

    text_lower = (post.get("full_text") or post.get("text") or "").lower()

    # Keyword score
    keyword_hits = sum(1 for kw in HIRING_KEYWORDS if kw in text_lower)
    strong_hits = sum(1 for kw in STRONG_SIGNALS if kw in text_lower)
    max_kw = len(HIRING_KEYWORDS)
    keyword_score = min((keyword_hits / max_kw) * 0.8 + strong_hits * 0.05, 1.0)

    # Recency score (last 24h = 1.0, 7 days = 0.2)
    now = time.time()
    age_hours = (now - post.get("timestamp", 0)) / 3600
    if age_hours <= 1:
        recency_score = 1.0
    elif age_hours <= 24:
        recency_score = 0.8
    elif age_hours <= 72:
        recency_score = 0.5
    elif age_hours <= 168:
        recency_score = 0.2
    else:
        recency_score = 0.05

    # Engagement score (normalise to 0-1, cap at 500 interactions)
    interactions = post.get("likes", 0) + post.get("comments", 0) * 2
    engagement_score = min(interactions / 500, 1.0)

    total = (
        keyword_score * weights["keyword_match"]
        + recency_score * weights["recency"]
        + engagement_score * weights["engagement"]
    )
    return round(total, 2)


def rank(posts: list[dict], config: dict) -> list[dict]:
    for post in posts:
        post["score"] = score(post, config)
    return sorted(posts, key=lambda p: p["score"], reverse=True)
