#!/usr/bin/env python3
"""Сборка сайта: content/*.json + src/ → dist/

    python3 build.py            собрать сайт в dist/
    python3 build.py --serve    собрать и запустить локальный сервер http://localhost:4317

Нужен только Python 3.8+ без сторонних библиотек.
"""
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date
from urllib.parse import urlparse

from sitegen import pages
from sitegen.components import WARNINGS, is_placeholder

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")


def load(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
        return json.load(f)


def find_placeholders(obj, path=""):
    """Пути к значениям-заполнителям вида "[...]"."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not k.startswith("_"):
                yield from find_placeholders(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from find_placeholders(v, f"{path}[{i}]")
    elif is_placeholder(obj):
        yield f"{path} = {obj}"


def validate(site, categories, projects, calc):
    errors = []
    ids = [c["id"] for c in categories]
    if len(ids) != len(set(ids)):
        errors.append("categories.json: повторяющиеся id")
    pids = [p["id"] for p in projects]
    if len(pids) != len(set(pids)):
        errors.append("projects.json: повторяющиеся id")
    for p in projects:
        for c in p.get("categories", []):
            if c not in ids:
                errors.append(f"projects.json: проект {p['id']} ссылается на неизвестное направление {c}")
    field_ids = [f["id"] for s in calc["steps"] for f in s["fields"]]
    for need in ("buildingType", "technology"):
        if need not in field_ids:
            errors.append(f"calculator.json: форма заявки использует поле {need}, его нет в схеме")
    if site["leads"].get("transport") not in ("none", "http"):
        errors.append("site.json: leads.transport должен быть \"none\" или \"http\"")
    return errors


def assets_hash():
    h = hashlib.sha1()
    for base in ("css", "js"):
        for dp, _, files in sorted(os.walk(os.path.join(SRC, "assets", base))):
            for fn in sorted(files):
                with open(os.path.join(dp, fn), "rb") as f:
                    h.update(f.read())
    return h.hexdigest()[:8]


ATTR_RE = re.compile(r'(\s(?:href|src|data-src|action)=")/(?!/)')
SRCSET_RE = re.compile(r'(\s(?:srcset|data-srcset)=")([^"]*)"')


def rebase(html, base):
    """Добавляет базовый путь (например, /IS) ко всем ссылкам от корня сайта."""
    if not base:
        return html
    html = ATTR_RE.sub(lambda m: m.group(1) + base + "/", html)
    return SRCSET_RE.sub(lambda m: m.group(1) + re.sub(
        r"(^|,\s*)/(?!/)", lambda n: n.group(1) + base + "/", m.group(2)) + '"', html)


def site_base(site):
    return urlparse(site["seo"]["siteUrl"]).path.rstrip("/")


def write(rel, text):
    rel = rel.lstrip("/")
    path = os.path.join(DIST, rel, "index.html") if not rel.endswith((".html", ".xml", ".txt")) else os.path.join(DIST, rel)
    if rel == "":
        path = os.path.join(DIST, "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build():
    site = load("site.json")
    categories = [c for c in load("categories.json")["items"] if c.get("published", True)]
    all_categories = load("categories.json")["items"]
    projects = [p for p in load("projects.json")["items"] if p.get("published", True)]
    home = load("home.json")
    calc = load("calculator.json")

    errors = validate(site, all_categories, projects, calc)
    if errors:
        print("Ошибки в контенте:\n  " + "\n  ".join(errors))
        sys.exit(1)

    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(DIST, "assets"))
    for fn in os.listdir(os.path.join(SRC, "static")):
        shutil.copy2(os.path.join(SRC, "static", fn), os.path.join(DIST, fn))

    ctx = pages.Ctx(site, categories, projects, home, calc, assets_hash())
    out = [pages.home_page(ctx), pages.catalog_page(ctx), pages.calculator_page(ctx),
           pages.contacts_page(ctx), pages.privacy_page(ctx), pages.not_found_page(ctx)]
    out += [pages.category_page(ctx, c) for c in categories]
    out += [pages.project_page(ctx, p) for p in projects]

    for path, html, _ in out:
        write(path, rebase(html, site_base(site)))

    base = site["seo"]["siteUrl"].rstrip("/")
    today = date.today().isoformat()
    urls = "".join(f"  <url><loc>{base}{path}</loc><lastmod>{today}</lastmod></url>\n"
                   for path, _, index in out if index)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n'
                         f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nDisallow: {site_base(site)}/api/\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")

    print(f"Готово: {len(out)} страниц → dist/  (в sitemap: {sum(1 for o in out if o[2])})")
    placeholders = list(find_placeholders(site))
    if placeholders:
        print("\nНе заполнено в content/site.json:")
        for p in placeholders:
            print("  ·", p)
    if "example.ru" in site["seo"]["siteUrl"] or "github.io" in site["seo"]["siteUrl"]:
        print(f"  · seo.siteUrl = {site['seo']['siteUrl']} — замените на свой домен, когда он появится")
    if site["leads"]["transport"] == "none":
        print("  · leads.transport = none — отправка заявок не подключена")
    demo = [p["id"] for p in projects if p.get("demo")]
    if demo:
        print(f"\nДемонстрационных проектов: {len(demo)} (закрыты от индексации)")
    for w in sorted(set(WARNINGS)):
        print("  ! " + w)


def serve(base, port=4317):
    """Локальный сервер, который, как и хостинг, отдаёт сайт по базовому пути."""
    import functools
    import http.server

    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            if base and (path == base or path.startswith(base + "/")):
                path = path[len(base):] or "/"
            return super().translate_path(path)

    handler = functools.partial(Handler, directory=DIST)
    print(f"http://localhost:{port}{base}/")
    http.server.ThreadingHTTPServer(("", port), handler).serve_forever()


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        serve(site_base(load("site.json")))
