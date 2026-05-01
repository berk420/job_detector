import requests


def send_message(token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            return True
        print(f"Telegram error {resp.status_code}: {resp.text}")
        return False
    except Exception as e:
        print(f"Telegram request failed: {e}")
        return False


def format_post(post: dict) -> str:
    author = post.get("author_name", "Bilinmeyen")
    title = post.get("author_title", "")
    text = post.get("text", "")
    url = post.get("url", "")
    likes = post.get("likes", 0)
    comments = post.get("comments", 0)

    header = f"<b>🔔 Yeni İlan — {author}</b>"
    if title:
        header += f"\n<i>{title}</i>"

    body = f"\n\n{text}"
    stats = f"\n\n👍 {likes}  💬 {comments}"
    link = f'\n\n<a href="{url}">LinkedIn\'de Görüntüle →</a>'

    return header + body + stats + link


def notify_new_posts(token: str, chat_id: str, posts: list[dict]) -> int:
    sent = 0
    for post in posts:
        msg = format_post(post)
        if send_message(token, chat_id, msg):
            sent += 1
    return sent
