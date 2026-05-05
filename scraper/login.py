"""
LinkedIn email/password login — returns li_at session cookie.
Uses the standard web login flow (no browser required).
"""

import re
import requests


def get_li_at(email: str, password: str) -> str:
    """Log in to LinkedIn and return the li_at session cookie value."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    })

    # Step 1: Get login page to extract CSRF token
    resp = session.get("https://www.linkedin.com/login", timeout=20)
    resp.raise_for_status()

    csrf_match = re.search(r'name="loginCsrfParam"\s+value="([^"]+)"', resp.text)
    if not csrf_match:
        raise RuntimeError("Could not find loginCsrfParam on login page — LinkedIn may have changed their flow")
    csrf = csrf_match.group(1)

    # Step 2: Submit credentials
    payload = {
        "session_key": email,
        "session_password": password,
        "loginCsrfParam": csrf,
        "isJsEnabled": "false",
        "trk": "guest_homepage-basic_nav-header-signin",
    }

    login_resp = session.post(
        "https://www.linkedin.com/checkpoint/lg/login-submit",
        data=payload,
        timeout=20,
        allow_redirects=True,
    )

    li_at = session.cookies.get("li_at")
    if not li_at:
        # Check for challenge/verification page
        if "checkpoint" in login_resp.url or "challenge" in login_resp.url:
            raise RuntimeError(
                "LinkedIn triggered a security challenge (2FA or CAPTCHA). "
                "Please log in manually via browser, then copy the li_at cookie value."
            )
        raise RuntimeError(
            f"Login failed — li_at cookie not found. "
            f"Final URL: {login_resp.url}"
        )

    return li_at
