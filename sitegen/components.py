"""Переиспользуемые фрагменты разметки."""
import glob
import html
import json
import os
from urllib.parse import urlencode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "src", "assets", "img")
WARNINGS = []


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def is_placeholder(v):
    return isinstance(v, str) and v.strip().startswith("[")


def filled(v):
    """Значение заполнено по-настоящему (не пустое и не заполнитель)."""
    return bool(v) and not is_placeholder(v)


def json_script(data, el_id=None, typ="application/json", attrs=""):
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    id_attr = f' id="{el_id}"' if el_id else ""
    return f'<script type="{typ}"{id_attr}{attrs}>{raw}</script>'


def calc_url(preset):
    preset = {k: v for k, v in (preset or {}).items() if v}
    return "/kalkulyator/" + ("?" + urlencode(preset) if preset else "")


ARROW = ('<svg class="icon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">'
         '<path d="M4 12h15M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>')


# ── Изображения ──────────────────────────────────────────────────────────
def _variants(src):
    """Ищет файлы <src>-<ширина>.(webp|jpg|jpeg|png). Возвращает [(w, url)] по возрастанию."""
    out = []
    for path in glob.glob(os.path.join(IMG_DIR, src + "-*")):
        stem, ext = os.path.splitext(os.path.basename(path))
        w = stem.rsplit("-", 1)[-1]
        if w.isdigit() and ext.lower() in (".webp", ".jpg", ".jpeg", ".png"):
            out.append((int(w), "/assets/img/" + os.path.relpath(path, IMG_DIR).replace(os.sep, "/")))
    return sorted(out)


def img(src, alt, sizes="100vw", cls="", eager=False, ratio=(3, 2), position=None):
    """Адаптивное <img> c srcset. src — путь от src/assets/img без ширины и расширения
    (например, "demo/hero-cabin") или путь к одиночному файлу ("photos/house.jpg")."""
    variants = _variants(src)
    w, h = 1200, round(1200 * ratio[1] / ratio[0])
    if variants:
        srcset = ", ".join(f"{u} {vw}w" for vw, u in variants)
        default = next((u for vw, u in variants if vw >= 1280), variants[-1][1])
        set_attr = f' srcset="{srcset}" sizes="{esc(sizes)}"'
    elif os.path.isfile(os.path.join(IMG_DIR, src)):
        default, set_attr = "/assets/img/" + src, ""
    else:
        WARNINGS.append(f"Нет изображения: src/assets/img/{src}")
        default, set_attr = "", ""
    load = ' loading="eager" fetchpriority="high"' if eager else ' loading="lazy"'
    cls_attr = f' class="{cls}"' if cls else ""
    if position:  # точка фокуса кадра при обрезке, например "50% 20%"
        cls_attr += f' style="object-position:{esc(position)}"'
    return (f'<img{cls_attr} src="{default}"{set_attr} alt="{esc(alt)}" width="{w}" height="{h}"'
            f' decoding="async"{load}>')


def img_srcset(src):
    v = _variants(src)
    return ", ".join(f"{u} {w}w" for w, u in v), (next((u for w, u in v if w >= 1280), v[-1][1]) if v else "")


# ── Кнопки, заголовки ────────────────────────────────────────────────────
def btn(label, href, kind="primary", arrow=False, extra=""):
    return (f'<a class="btn btn--{kind}" href="{esc(href)}"{extra}>'
            f'<span>{esc(label)}</span>{ARROW if arrow else ""}</a>')


def section_head(eyebrow=None, title="", text=None, tag="h2", cls="", title_id=None):
    eb = f'<p class="eyebrow">{esc(eyebrow)}</p>' if eyebrow else ""
    tx = f'<p class="section-head__text">{esc(text)}</p>' if text else ""
    tid = f' id="{title_id}"' if title_id else ""
    return (f'<header class="section-head {cls}" data-reveal>{eb}'
            f'<{tag} class="section-head__title"{tid}>{esc(title)}</{tag}>{tx}</header>')


def breadcrumbs(items):
    """items: [(label, href|None)]"""
    lis = []
    for label, href in items:
        if href:
            lis.append(f'<li><a href="{esc(href)}">{esc(label)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{esc(label)}</li>')
    return f'<nav class="breadcrumbs" aria-label="Навигационная цепочка"><ol>{"".join(lis)}</ol></nav>'


# ── Направления ──────────────────────────────────────────────────────────
def direction_card(cat, i, n):
    if i == 0:
        size = "lg"
    elif i == 1:
        size = "md"
    elif i == n - 1 and (n - 2) % 3 == 1:
        size = "wide"
    else:
        size = "sm"
    sizes = {"lg": "(min-width: 960px) 58vw, 100vw", "md": "(min-width: 960px) 42vw, 100vw",
             "wide": "(min-width: 960px) 50vw, 100vw", "sm": "(min-width: 960px) 33vw, 100vw"}[size]
    tags = "".join(f"<li>{esc(f['title'])}</li>" for f in cat.get("features", [])[:3])
    return f"""
<article class="dir-card dir-card--{size}" data-reveal>
  <div class="dir-card__media">{img(cat['image']['src'], cat['image']['alt'], sizes, position=cat['image'].get('position'))}</div>
  <div class="dir-card__body">
    <p class="dir-card__num">{i + 1:02d}</p>
    <h3 class="dir-card__title"><a href="/uslugi/{cat['id']}/">{esc(cat['title'])}</a></h3>
    <p class="dir-card__lead">{esc(cat['lead'])}</p>
    {f'<ul class="tag-list">{tags}</ul>' if tags else ''}
    <div class="dir-card__actions">
      <a class="text-link" href="/proekty/?cat={cat['id']}">Проекты</a>
      <a class="text-link" href="{esc(calc_url(cat.get('calcPreset')))}">Рассчитать</a>
    </div>
  </div>
</article>"""


# ── Проекты ──────────────────────────────────────────────────────────────
def fmt_area(a):
    if a in (None, ""):
        return ""
    s = f"{a:g}".replace(".", ",") if isinstance(a, (int, float)) else str(a)
    return f"{s} м²"


def fmt_price(p):
    return f"{p:,.0f}".replace(",", " ") + " ₽"


def project_specs(p):
    items = [fmt_area(p.get("area")), p.get("floors"), p.get("dimensions") if p.get("dimensions") not in (None, "", "—") else ""]
    return [x for x in items if x]


def demo_badge():
    return '<span class="badge badge--demo" title="Демонстрационная карточка — не реальный объект компании">Демо</span>'


def project_card(p, sizes="(min-width: 1080px) 33vw, (min-width: 640px) 50vw, 100vw", attrs=""):
    image = p["images"][0] if p.get("images") else {"src": "", "alt": ""}
    specs = "".join(f"<li>{esc(s)}</li>" for s in project_specs(p))
    price = (f'<p class="project-card__price">{fmt_price(p["price"])}</p>'
             if isinstance(p.get("price"), (int, float)) else "")
    meta = " · ".join(x for x in (p.get("type"), p.get("technology")) if x)
    return f"""
<article class="project-card"{attrs}>
  <div class="project-card__media">{img(image['src'], image['alt'], sizes, ratio=(4, 3), position=image.get('position'))}{demo_badge() if p.get('demo') else ''}</div>
  <div class="project-card__body">
    <p class="project-card__meta">{esc(meta)}</p>
    <h3 class="project-card__title"><a href="/proekty/{p['id']}/">{esc(p['title'])}</a></h3>
    <ul class="project-card__specs">{specs}</ul>
    {price}
  </div>
</article>"""


# ── Форма заявки ─────────────────────────────────────────────────────────
def _options(field, selected=None):
    opts = ['<option value="">Не выбрано</option>']
    for o in field.get("options", []):
        sel = " selected" if selected == o["value"] else ""
        opts.append(f'<option value="{esc(o["value"])}"{sel}>{esc(o["label"])}</option>')
    return "".join(opts)


def lead_form(ctx, calc_schema, site, source, prefix, project=None, preset=None, submit="Отправить заявку"):
    fields = {f["id"]: f for s in calc_schema["steps"] for f in s["fields"]}
    preset = preset or {}
    p = prefix
    policy = site["legal"].get("privacyPolicyUrl") or "#"

    def text_field(name, label, typ="text", auto="", extra="", required=True):
        req = ' aria-required="true"' if required else ""
        return f"""
    <div class="field">
      <label class="field__label" for="{p}-{name}">{label}</label>
      <input class="input" id="{p}-{name}" name="{name}" type="{typ}" {auto}{req} aria-describedby="{p}-{name}-err" {extra}>
      <p class="field__error" id="{p}-{name}-err" hidden></p>
    </div>"""

    project_input = f'<input type="hidden" name="project" value="{esc(project)}">' if project else ""
    return f"""
<form class="lead-form" data-lead-form novalidate aria-label="Заявка на консультацию">
  <input type="hidden" name="source" value="{esc(source)}">{project_input}
  <div class="lead-calc" data-lead-calc hidden></div>
  <div class="lead-form__grid">
    {text_field("name", "Имя", auto='autocomplete="name" maxlength="80"')}
    {text_field("phone", "Телефон", typ="tel", auto='autocomplete="tel" inputmode="tel" placeholder="+7"')}
    <div class="field">
      <label class="field__label" for="{p}-buildingType">Тип строения</label>
      <div class="select-wrap"><select class="input" id="{p}-buildingType" name="buildingType">{_options(fields["buildingType"], preset.get("buildingType"))}</select></div>
    </div>
    <div class="field">
      <label class="field__label" for="{p}-technology">Предпочтительная технология</label>
      <div class="select-wrap"><select class="input" id="{p}-technology" name="technology">{_options(fields["technology"], preset.get("technology"))}</select></div>
    </div>
    <div class="field field--full">
      <label class="field__label" for="{p}-message">Дополнительные пожелания <span class="field__optional">необязательно</span></label>
      <textarea class="input" id="{p}-message" name="message" rows="4" maxlength="2000" aria-describedby="{p}-message-err"></textarea>
      <p class="field__error" id="{p}-message-err" hidden></p>
    </div>
  </div>
  <div class="hp" aria-hidden="true"><label>Сайт<input name="website" type="text" tabindex="-1" autocomplete="off"></label></div>
  <div class="field field--check">
    <label class="check"><input type="checkbox" name="consent" aria-describedby="{p}-consent-err">
      <span>Согласен(на) на обработку персональных данных в соответствии с <a href="{esc(policy)}">политикой конфиденциальности</a></span></label>
    <p class="field__error" id="{p}-consent-err" hidden></p>
  </div>
  <div class="lead-form__footer">
    <button class="btn btn--primary btn--block" type="submit"><span>{esc(submit)}</span></button>
  </div>
  <div class="lead-status" data-lead-status role="status" aria-live="polite" hidden></div>
</form>"""


# ── Контакты ─────────────────────────────────────────────────────────────
def phone_link(site, cls=""):
    c = site["contacts"]
    cls_attr = f' class="{cls}"' if cls else ""
    if filled(c.get("phoneHref")):
        return f'<a{cls_attr} href="tel:{esc(c["phoneHref"])}">{esc(c["phone"])}</a>'
    return f'<span{cls_attr}>{esc(c["phone"])}</span>' if c.get("phone") else ""


def messengers(site, cls="messengers"):
    items = []
    for m in site["contacts"].get("messengers", []):
        if filled(m.get("url")):
            items.append(f'<li><a href="{esc(m["url"])}" target="_blank" rel="noopener">{esc(m["label"])}</a></li>')
        else:
            items.append(f'<li><span title="Ссылка не указана">{esc(m["label"])}</span></li>')
    return f'<ul class="{cls}">{"".join(items)}</ul>' if items else ""


def contact_rows(site):
    c, r = site["contacts"], site["region"]
    rows = [
        ("Телефон", phone_link(site)),
        ("Мессенджеры", messengers(site)),
        ("Почта", (f'<a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a>' if filled(c.get("email")) else esc(c.get("email")))),
        ("Регион работы", esc(r.get("name"))),
        ("Часы работы", esc(c.get("hours"))),
        ("Адрес", esc(c.get("address"))),
    ]
    return "".join(f'<div class="contact-row"><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows if v)
