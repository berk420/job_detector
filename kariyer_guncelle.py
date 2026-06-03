"""CV'yi kariyer.net'te her 5 dakikada bir günceller — python kariyer_guncelle.py"""

import os
import sys
import time

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
from datetime import datetime
from scraper.kariyer import update_cv

INTERVAL = 5 * 60  # saniye

if __name__ == "__main__":
    print("Basladi. Her 5 dakikada bir CV guncellenecek. Durdurmak icin Ctrl+C.")
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] Calistiriliyor...")
        try:
            update_cv()
        except Exception as e:
            print(f"Hata: {e} — {INTERVAL//60} dakika sonra tekrar deneniyor.")
        print(f"Sonraki guncelleme {INTERVAL//60} dakika sonra.")
        time.sleep(INTERVAL)
