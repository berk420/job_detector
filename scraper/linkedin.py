import requests
import json
import time
import re
from typing import Optional


class LinkedInSearcher:
    VOYAGER_BASE = "https://www.linkedin.com/voyager/api"

    def __init__(self, li_at: str):
        self.li_at = li_at
        self.session = requests.Session()
        self.session.cookies.set("li_at", li_at, domain=".linkedin.com")
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/vnd.linkedin.normalized+json+2.1",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "X-RestLi-Protocol-Version": "2.0.0",
            "X-Li-Lang": "tr_TR",
            "X-Li-Track": json.dumps({
                "clientVersion": "1.13.9753",
                "osName": "web",
                "timezoneOffset": 3,
                "timezone": "Europe/Istanbul",
                "deviceFormFactor": "DESKTOP",
            }),
        })

    def authenticate(self) -> bool:
        """Visit LinkedIn home to get JSESSIONID and set CSRF token."""
        try:
            resp = self.session.get(
                "https://www.linkedin.com/",
                timeout=20,
                allow_redirects=True,
            )
            jsessionid = self.session.cookies.get("JSESSIONID", "")
            if not jsessionid:
                match = re.search(r'"JSESSIONID"\s*:\s*"([^"]+)"', resp.text)
                if match:
                    jsessionid = match.group(1)
            if jsessionid:
                csrf = jsessionid.strip('"')
                self.session.headers["Csrf-Token"] = csrf
                self.session.cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com")
                print(f"Auth OK — CSRF token acquired")
                return True
            print("Warning: JSESSIONID not found, trying without CSRF token")
            return False
        except Exception as e:
            print(f"Auth error: {e}")
            return False

    def search_content(self, keywords: str, count: int = 25) -> list[dict]:
        """Search LinkedIn posts using Voyager API."""
        self.authenticate()
        time.sleep(2)

        params = {
            "decorationId": "com.linkedin.voyager.deco.search.SearchClusterCollection-54",
            "count": count,
            "filters": "List(resultType->CONTENT,sortBy->DD)",
            "keywords": keywords,
            "origin": "FACETED_SEARCH",
            "q": "blended",
            "start": 0,
        }

        try:
            resp = self.session.get(
                f"{self.VOYAGER_BASE}/search/blended",
                params=params,
                timeout=25,
                headers={"Referer": "https://www.linkedin.com/search/results/content/"},
            )
            if resp.status_code == 401:
                print("Error: li_at cookie expired or invalid")
                return []
            if resp.status_code != 200:
                print(f"LinkedIn API returned {resp.status_code}")
                return []

            data = resp.json()
            return self._parse_response(data)

        except requests.Timeout:
            print("LinkedIn request timed out")
            return []
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _parse_response(self, data: dict) -> list[dict]:
        """Parse Voyager API blended search response."""
        included_by_urn: dict[str, dict] = {}
        for item in data.get("included", []):
            if isinstance(item, dict):
                urn = item.get("entityUrn") or item.get("urn", "")
                if urn:
                    included_by_urn[urn] = item

        posts = []
        seen_urns: set[str] = set()

        # Primary path: elements → clusters → hits
        for cluster in data.get("data", {}).get("elements", []):
            if not isinstance(cluster, dict):
                continue
            for hit in cluster.get("elements", []):
                if not isinstance(hit, dict):
                    continue
                urn = hit.get("targetUrn", "")
                if not urn or urn in seen_urns:
                    continue
                entity = included_by_urn.get(urn, {})
                post = self._extract_post(entity, urn)
                if post:
                    posts.append(post)
                    seen_urns.add(urn)

        # Fallback: scan included array for post-like entities
        if not posts:
            for urn, entity in included_by_urn.items():
                etype = entity.get("$type", "")
                if any(t in etype for t in ["Update", "Share", "Article"]):
                    if urn not in seen_urns:
                        post = self._extract_post(entity, urn)
                        if post:
                            posts.append(post)
                            seen_urns.add(urn)

        print(f"Found {len(posts)} posts")
        return posts

    def _extract_post(self, entity: dict, urn: str) -> Optional[dict]:
        text = self._deep_text(entity, [
            ["commentary", "text", "text"],
            ["commentary", "text"],
            ["text", "text"],
            ["text"],
            ["description", "text"],
        ])
        if not text or len(text) < 20:
            return None

        actor = entity.get("actor", {})
        author_name = self._get_text(actor.get("name", {}))
        author_title = self._get_text(actor.get("description", {}))

        url = f"https://www.linkedin.com/feed/update/{urn}/"

        ts = entity.get("createdAt") or entity.get("publishedAt") or 0
        if ts > 1_000_000_000_000:
            ts = ts // 1000

        social = entity.get("socialDetail") or {}
        likes = int(social.get("totalLikes") or social.get("numLikes") or 0)
        comments = int(social.get("numComments") or social.get("totalComments") or 0)

        return {
            "id": urn,
            "text": text[:350] + "…" if len(text) > 350 else text,
            "full_text": text,
            "author_name": author_name,
            "author_title": author_title,
            "url": url,
            "timestamp": int(ts),
            "likes": likes,
            "comments": comments,
        }

    def _deep_text(self, obj: dict, paths: list[list[str]]) -> str:
        for path in paths:
            cur = obj
            for key in path:
                if isinstance(cur, dict):
                    cur = cur.get(key, "")
                else:
                    cur = ""
                    break
            if isinstance(cur, str) and cur.strip():
                return cur.strip()
        return ""

    def _get_text(self, obj) -> str:
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            return obj.get("text") or obj.get("value") or ""
        return ""
