"""Каркас страницы: <head> с SEO, шапка, подвал, подключение скриптов."""
from datetime import date
from urllib.parse import urlparse

from .components import (esc, filled, json_script, phone_link, messengers, contact_rows, btn)


def _abs(site, path):
    return site["seo"]["siteUrl"].rstrip("/") + path


def page_title(site, title):
    suffix = site["seo"].get("titleSuffix")
    if title and filled(suffix):
        return f"{title} — {suffix}"
    return title or site["seo"]["defaultTitle"]


def org_jsonld(site):
    c, co = site["contacts"], site["company"]
    data = {"@context": "https://schema.org", "@type": "HomeAndConstructionBusiness",
            "url": site["seo"]["siteUrl"]}
    if filled(co.get("name")):
        data["name"] = co["name"]
    if filled(c.get("phoneHref")):
        data["telephone"] = c["phoneHref"]
    if filled(c.get("email")):
        data["email"] = c["email"]
    if filled(site["region"].get("name")):
        data["areaServed"] = site["region"]["name"]
    if filled(c.get("address")):
        data["address"] = c["address"]
    links = [m["url"] for m in c.get("messengers", []) if filled(m.get("url"))]
    if links:
        data["sameAs"] = links
    return data


def metrika(site):
    mid = str(site["analytics"].get("yandexMetrikaId") or "").strip()
    if not mid.isdigit():
        return ""
    webvisor = "true" if site["analytics"].get("webvisor") else "false"
    return f"""<script>
window.__ymId={mid};
(function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){{if(document.scripts[j].src===r){{return;}}}}
k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})
(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");
ym({mid},"init",{{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:{webvisor}}});
</script><noscript><div><img src="https://mc.yandex.ru/watch/{mid}" style="position:absolute;left:-9999px" alt=""></div></noscript>"""


def header(site, overlay):
    nav = "".join(f'<li><a href="{esc(n["href"])}">{esc(n["label"])}</a></li>' for n in site["nav"])
    name = site["company"].get("shortName") or site["company"].get("name")
    return f"""
<header class="site-header{' site-header--overlay' if overlay else ''}" data-header>
  <div class="container site-header__inner">
    <a class="logo" href="/" aria-label="{esc(site['company']['name'])} — на главную">
      <svg class="logo__mark" viewBox="0 0 32 32" width="30" height="30" aria-hidden="true"><path d="M3 15 16 4l13 11M7 12v15h18V12M13 27v-8h6v8" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>
      <span class="logo__text">{esc(name)}</span>
    </a>
    <nav class="site-nav" id="site-menu" aria-label="Основное меню">
      <ul class="site-nav__list">{nav}</ul>
      <div class="site-nav__extra">
        {phone_link(site, 'site-nav__phone')}
        {messengers(site, 'messengers messengers--menu')}
        {btn('Рассчитать стоимость', '/kalkulyator/', 'primary')}
      </div>
    </nav>
    <div class="site-header__actions">
      {phone_link(site, 'site-header__phone')}
      {btn('Рассчитать', '/kalkulyator/', 'primary', extra=' data-header-cta')}
      <button class="burger" type="button" data-menu-toggle aria-expanded="false" aria-controls="site-menu" aria-label="Открыть меню"><span></span><span></span></button>
    </div>
  </div>
</header>"""


def footer(site, categories):
    cats = "".join(f'<li><a href="/uslugi/{c["id"]}/">{esc(c["title"])}</a></li>' for c in categories)
    nav = "".join(f'<li><a href="{esc(n["href"])}">{esc(n["label"])}</a></li>' for n in site["nav"])
    co = site["company"]
    legal = " · ".join(x for x in (
        co.get("legalName"), f"ИНН {co['inn']}" if co.get("inn") else "", f"ОГРН {co['ogrn']}" if co.get("ogrn") else "") if x)
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="site-footer__top">
      <div class="site-footer__brand">
        <p class="site-footer__name">{esc(co['name'])}</p>
        <p class="site-footer__tagline">Строительство загородных домов и бань</p>
        {btn('Рассчитать стоимость', '/kalkulyator/', 'light', arrow=True)}
      </div>
      <nav class="site-footer__col" aria-label="Направления"><p class="site-footer__h">Направления</p><ul>{cats}</ul></nav>
      <nav class="site-footer__col" aria-label="Разделы сайта"><p class="site-footer__h">Разделы</p><ul>{nav}</ul></nav>
      <div class="site-footer__col"><p class="site-footer__h">Контакты</p><dl class="contact-list contact-list--footer">{contact_rows(site)}</dl></div>
    </div>
    <div class="site-footer__bottom">
      <p>© {date.today().year} {esc(co['name'])}{' · ' + esc(legal) if legal else ''}</p>
      <p><a href="{esc(site['legal']['privacyPolicyUrl'])}">Политика конфиденциальности</a></p>
      <p class="site-footer__credit">{esc(site['legal'].get('photoCredit', ''))}</p>
    </div>
  </div>
</footer>"""


def page(site, categories, *, path, title, description, body, overlay=False, noindex=False,
         og_image=None, jsonld=None, assets_version="", body_class=""):
    full_title = page_title(site, title)
    canonical = _abs(site, path)
    og = _abs(site, og_image or site["seo"]["ogImage"])
    ld = [org_jsonld(site)] + (jsonld or [])
    base = urlparse(site["seo"]["siteUrl"]).path.rstrip("/")
    leads = {k: v for k, v in site["leads"].items() if not k.startswith("_")}
    if str(leads.get("endpoint", "")).startswith("/"):
        leads["endpoint"] = base + leads["endpoint"]
    client_cfg = {
        "base": base,
        "leads": leads,
        "contacts": {
            "phone": site["contacts"].get("phone"),
            "phoneHref": site["contacts"].get("phoneHref") if filled(site["contacts"].get("phoneHref")) else "",
            "messengers": [m for m in site["contacts"].get("messengers", []) if filled(m.get("url"))],
        },
    }
    robots = '<meta name="robots" content="noindex, follow">' if noindex else ""
    v = f"?v={assets_version}" if assets_version else ""
    return f"""<!doctype html>
<html lang="{site['seo'].get('language', 'ru')}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
{robots}
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{esc(title or full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og)}">
{f'<meta property="og:site_name" content="{esc(site["company"]["name"])}">' if filled(site["company"]["name"]) else ''}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1f3a2e">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/manrope-normal-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/cormorant-normal-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/fonts.css">
<link rel="stylesheet" href="/assets/css/main.css{v}">
<script type="module" src="/assets/js/main.js{v}"></script>
{"".join(json_script(x, typ="application/ld+json") for x in ld)}
{metrika(site)}
</head>
<body class="{body_class}">
<a class="skip-link" href="#main">Перейти к содержимому</a>
{header(site, overlay)}
<main id="main">
{body}
</main>
{footer(site, categories)}
{json_script(client_cfg, "site-config")}
</body>
</html>
"""
