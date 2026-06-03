"""
kariyer.net CV güncelle otomasyonu.
Credentials: KARIYER_EMAIL, KARIYER_PASSWORD (.env'den)

İlk çalıştırmada tarayıcı görünür açılır, CAPTCHA'yı siz çözüp giriş yaparsınız.
Giriş sonrası cookies otomatik kaydedilir, sonraki çalışmalarda tekrar login gerekmez.
"""

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

CV_UPDATE_XPATH = '//*[@id="resume-list-section"]/div[1]/section/div[1]/div/div[1]/div/button'
HESABIM_URL = "https://www.kariyer.net/hesabim"
LOGIN_URL = "https://www.kariyer.net/aday/giris"
COOKIES_FILE = Path(__file__).parent.parent / "data" / "kariyer_cookies.json"


def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def save_cookies(ctx):
    COOKIES_FILE.parent.mkdir(exist_ok=True)
    cookies = ctx.cookies()
    COOKIES_FILE.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Cookies kaydedildi.")


def load_cookies(ctx):
    if not COOKIES_FILE.exists():
        return False
    cookies = json.loads(COOKIES_FILE.read_text(encoding="utf-8"))
    same_site_map = {
        "no_restriction": "None",
        "unspecified": "None",
        "lax": "Lax",
        "strict": "Strict",
        "none": "None",
    }
    cleaned = []
    for c in cookies:
        if "sameSite" in c:
            c["sameSite"] = same_site_map.get(str(c["sameSite"]).lower(), "None")
        # Cookie-Editor uses "storeId", "hostOnly" etc. — Playwright doesn't need them
        for key in ("storeId", "hostOnly", "session", "id"):
            c.pop(key, None)
        cleaned.append(c)
    ctx.add_cookies(cleaned)
    return True


def is_logged_in(page) -> bool:
    return "hesabim" in page.url and "giris" not in page.url


def update_cv():
    env = load_env()
    headless_env = env.get("HEADLESS", os.environ.get("HEADLESS", "true")).lower()
    headless = headless_env != "false"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        # Kaydedilmis cookie varsa kullan
        if load_cookies(ctx):
            print("Kaydedilmis session yukleniyor...")
            page.goto(HESABIM_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
        else:
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=40000)

        # Giris yapilmamissa
        if not is_logged_in(page):
            print("Giris gerekli. Tarayici aciliyor...")
            if headless:
                # Headless modda gorsel tarayici acilamaz, hata ver
                browser.close()
                raise RuntimeError(
                    "Oturum acik degil ve HEADLESS=true. "
                    "Ilk giris icin .env dosyasina HEADLESS=false ekleyin, "
                    "scripti calistirin, CAPTCHA'yi cozun ve girisin tamamlanmasini bekleyin."
                )

            # Gorunen tarayici: kullanici giris yapsin
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=40000)
            print("Lutfen tarayicida giris yapin ve CAPTCHA'yi cozun...")
            print("Giris tamamlaninca bu pencere otomatik kapanacak.")
            print("=" * 50)
            print("YAPMANIZ GEREKEN:")
            print("1. Acilan Firefox penceresinde giris yapin")
            print("2. CAPTCHA slider'ini cozun")
            print("3. 'Giris Yap' butonuna basin")
            print("5 dakika bekleniyor...")
            print("=" * 50)
            try:
                page.wait_for_url("**/hesabim**", timeout=300000)
            except PlaywrightTimeout:
                browser.close()
                raise RuntimeError("5 dakika icinde giris tamamlanamadi.")

            save_cookies(ctx)
            print("Giris basarili, cookies kaydedildi.")

        # Hesabim sayfasindayiz, CV guncelle butonunu bul
        print("CV guncelle butonu aranıyor...")
        btn = page.locator(f'xpath={CV_UPDATE_XPATH}')
        btn.wait_for(timeout=15000)
        btn_text = btn.inner_text()
        print(f"Buton bulundu: '{btn_text}' — modal kapatiliyor...")

        # Reklam/banner modal varsa kapat
        page.evaluate("document.querySelectorAll('[id*=\"banner\"][role=\"dialog\"], .modal.show').forEach(el => el.remove())")
        page.wait_for_timeout(800)

        # JavaScript ile tıkla (force click yerine gerçek DOM event)
        print("Tiklaniyor...")
        page.evaluate(f"""
            const btn = document.evaluate(
                '{CV_UPDATE_XPATH}', document, null,
                XPathResult.FIRST_ORDERED_NODE_TYPE, null
            ).singleNodeValue;
            if (btn) btn.click();
        """)
        page.wait_for_timeout(3000)
        print("CV guncellendi!")

        # Cookies yenile
        save_cookies(ctx)

        if not headless:
            print("Tarayici acik kaliyor. Kapatmak icin bu terminale Enter basin...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                pass

        browser.close()
