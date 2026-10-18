#!/usr/bin/env python3
"""Скачивает демонстрационные фото (Unsplash License) в src/assets/img/demo/.

Это иллюстрации, а не объекты компании. Замените их реальными фотографиями:
положите файлы вида  <имя>-640.webp, <имя>-1280.webp, <имя>-1920.webp
(или .jpg) в src/assets/img/ и укажите "<папка>/<имя>" в content/*.json.
Для нарезки своих фото есть tools/optimize_images.sh.

Запуск:  python3 tools/fetch_demo_images.py
"""
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "assets", "img", "demo")
WIDTHS = (640, 1280, 1920)
QUALITY = {640: 70, 1280: 62, 1920: 55}  # большие кадры сильнее сжимаем

# имя файла -> id фото на Unsplash
PHOTOS = {
    "hero-cabin": "1542718610-a1d656d1884c",
    "wood-house-forest": "1449844908441-8829872d2607",
    "frame-house-modern": "1600566753190-17f0baa2a6c3",
    "beam-house-forest": "1587061949409-02df41d5e562",
    "log-house-snow": "1510798831971-661eb04b3739",
    "banya-cabin": "1595521624992-48a59aef95e3",
    "outbuilding-red": "1518780664697-55e3ad937233",
    "roofing-works": "1632759145351-1d592919f522",
    "lake-house": "1470770841072-f978cf4d019e",
    "stone-cottage": "1588880331179-bc9b93a8cb5e",
    "house-lawn": "1475855581690-80accde3ae2b",
    "house-modern-dark": "1600585154340-be6161a56a0c",
    "house-dusk": "1568605114967-8130f3a36994",
    "interior-living": "1600210492486-724fe5c67fb0",
    "interior-light": "1501183638710-841dd1904471",
    "process-drawings": "1503387762-592deb58ef4e",
    "process-site": "1541888946425-d81bb19240f5",
    "process-worker": "1621905251189-08b45d6a269e",
}


def fetch(url, path):
    if os.path.exists(path):
        return
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        f.write(r.read())
    print("  ", os.path.relpath(path, ROOT))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, pid in PHOTOS.items():
        base = f"https://images.unsplash.com/photo-{pid}"
        for w in WIDTHS:
            h = round(w * 2 / 3)
            fetch(f"{base}?w={w}&h={h}&fit=crop&crop=entropy&fm=webp&q={QUALITY[w]}",
                  os.path.join(OUT, f"{name}-{w}.webp"))
    # Open Graph: 1200x630 JPEG (соцсети и мессенджеры не всегда понимают WebP)
    fetch("https://images.unsplash.com/photo-1542718610-a1d656d1884c?w=1200&h=630&fit=crop&fm=jpg&q=78",
          os.path.join(ROOT, "src", "assets", "img", "og-default.jpg"))


if __name__ == "__main__":
    main()
