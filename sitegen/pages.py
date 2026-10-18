"""Страницы сайта. Каждая функция возвращает (путь, html, индексировать_ли)."""
from .components import (ARROW, breadcrumbs, filled, btn, calc_url, contact_rows, direction_card, esc,
                         fmt_area, fmt_price, demo_badge, img, img_srcset, json_script, lead_form,
                         messengers, phone_link, project_card, section_head)
from .layout import page


class Ctx:
    def __init__(self, site, categories, projects, home, calc, assets_version):
        self.site = site
        self.categories = categories  # только опубликованные
        self.projects = projects  # только опубликованные
        self.home = home
        self.calc = calc
        self.v = assets_version

    def render(self, **kw):
        return page(self.site, self.categories, assets_version=self.v, **kw)

    def cat(self, cid):
        return next((c for c in self.categories if c["id"] == cid), None)


def bc_jsonld(site, items):
    base = site["seo"]["siteUrl"].rstrip("/")
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": label, **({"item": base + href} if href else {})}
        for i, (label, href) in enumerate(items)]}


def faq_jsonld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": it["q"], "acceptedAnswer": {"@type": "Answer", "text": it["a"]}}
        for it in items]}


# ── Общие блоки ──────────────────────────────────────────────────────────
def faq_block(items, open_first=False):
    return "".join(
        f'<details class="faq__item"{" open" if open_first and i == 0 else ""}>'
        f'<summary><span>{esc(it["q"])}</span><span class="faq__icon" aria-hidden="true"></span></summary>'
        f'<div class="faq__answer"><p>{esc(it["a"])}</p></div></details>'
        for i, it in enumerate(items))


def lead_section(ctx, source, prefix, project=None, preset=None, title=None, text=None):
    h = ctx.home["lead"]
    return f"""
<section class="section lead-section" id="zayavka" aria-labelledby="{prefix}-title">
  <div class="container lead-section__grid">
    <div class="lead-section__intro" data-reveal>
      <p class="eyebrow">{esc(h['eyebrow'])}</p>
      <h2 class="section-head__title" id="{prefix}-title">{esc(title or h['title'])}</h2>
      <p class="section-head__text">{esc(text or h['text'])}</p>
      <dl class="contact-list">{contact_rows(ctx.site)}</dl>
    </div>
    <div class="lead-section__form" data-reveal>
      {lead_form(ctx, ctx.calc, ctx.site, source, prefix, project=project, preset=preset)}
    </div>
  </div>
</section>"""


def calc_band(ctx, title=None):
    h = ctx.home["calculator"]
    bt = next(f for s in ctx.calc["steps"] for f in s["fields"] if f["id"] == "buildingType")
    choices = "".join(f"""
      <a class="calc-band__choice" href="{esc(calc_url({'buildingType': o['value']}))}">
        {img(o['image'], '', '(min-width: 960px) 14vw, 30vw') if o.get('image') else ''}
        <span class="calc-band__choice-label">{esc(o['label'])}</span>{ARROW}
      </a>""" for o in bt["options"])
    steps = "".join(f"<li>{esc(s)}</li>" for s in h["steps"])
    return f"""
<section class="section calc-band" aria-labelledby="calc-band-title">
  <div class="container calc-band__grid">
    <div class="calc-band__text" data-reveal>
      <p class="eyebrow eyebrow--light">{esc(h['eyebrow'])}</p>
      <h2 class="section-head__title" id="calc-band-title">{esc(title or h['title'])}</h2>
      <p class="section-head__text">{esc(h['text'])}</p>
      <ol class="calc-band__steps">{steps}</ol>
      {btn('Открыть калькулятор', '/kalkulyator/', 'light', arrow=True)}
    </div>
    <div class="calc-band__pick" data-reveal>
      <p class="calc-band__pick-title">Что вы планируете построить?</p>
      <div class="calc-band__choices">{choices}</div>
    </div>
  </div>
</section>"""


# ── Главная ──────────────────────────────────────────────────────────────
def home_page(ctx):
    h, site = ctx.home, ctx.site
    hero = h["hero"]
    dir_links = "".join(f'<li><a href="/uslugi/{c["id"]}/">{esc(c.get("navTitle") or c["title"])}</a></li>'
                        for c in ctx.categories)
    cards = "".join(direction_card(c, i, len(ctx.categories)) for i, c in enumerate(ctx.categories))
    featured = [p for p in ctx.projects if p.get("featured")] or ctx.projects[:6]
    proj = "".join(project_card(p, "(min-width: 960px) 30vw, 80vw") for p in featured)
    any_demo = any(p.get("demo") for p in featured)
    steps = "".join(f"""
      <li class="process__step" data-reveal><span class="process__num">{i + 1:02d}</span>
        <div><h3>{esc(s['title'])}</h3><p>{esc(s['text'])}</p></div></li>"""
                    for i, s in enumerate(h["process"]["steps"]))
    principles = "".join(f"""
      <li class="principles__item" data-reveal><span class="principles__num">{i + 1:02d}</span>
        <h3>{esc(p['title'])}</h3><p>{esc(p['text'])}</p></li>"""
                         for i, p in enumerate(h["principles"]["items"]))
    region = site["region"]["name"]
    region_sfx = f" · {esc(region)}" if filled(region) else ""

    body = f"""
<section class="hero">
  <div class="hero__media">{img(hero['image']['src'], hero['image']['alt'], '100vw', eager=True)}</div>
  <div class="container hero__inner">
    <div class="hero__content">
      <p class="eyebrow eyebrow--light">{esc(hero['eyebrow'])}{region_sfx}</p>
      <h1 class="hero__title">{esc(hero['title'])}</h1>
      <p class="hero__text">{esc(hero['text'])}</p>
      <div class="hero__actions">
        {btn(hero['primaryCta']['label'], hero['primaryCta']['href'], 'primary', arrow=True)}
        {btn(hero['secondaryCta']['label'], hero['secondaryCta']['href'], 'outline-light')}
      </div>
    </div>
    <nav class="hero__dirs" aria-label="Направления строительства"><ul>{dir_links}</ul></nav>
  </div>
</section>

<section class="section" id="napravleniya" aria-labelledby="dir-title">
  <div class="container">
    {section_head(h['directions']['eyebrow'], h['directions']['title'], h['directions']['text'], cls='section-head--split', title_id='dir-title')}
    <div class="dir-grid">{cards}</div>
  </div>
</section>

<section class="section section--sand" id="proekty" aria-labelledby="proj-title">
  <div class="container">
    <div class="section-head-row">
      {section_head(h['projects']['eyebrow'], h['projects']['title'], h['projects']['text'], title_id='proj-title')}
      <div class="scroller-ctrl" data-reveal>
        <button class="icon-btn" type="button" data-scroll-prev aria-label="Предыдущие проекты"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M20 12H5M11 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
        <button class="icon-btn" type="button" data-scroll-next aria-label="Следующие проекты">{ARROW}</button>
      </div>
    </div>
    {'<p class="note">Сейчас в каталоге демонстрационные карточки: фотографии — иллюстрации, а не объекты компании.</p>' if any_demo else ''}
  </div>
  <div class="scroller" data-scroller tabindex="0" aria-label="Проекты">{proj}</div>
  <div class="container section-foot">{btn('Все проекты', '/proekty/', 'outline', arrow=True)}</div>
</section>

{calc_band(ctx)}

<section class="section process" id="etapy" aria-labelledby="process-title">
  <div class="container process__grid">
    <div class="process__aside">
      {section_head(h['process']['eyebrow'], h['process']['title'], title_id='process-title')}
      <div class="process__media" data-reveal>{img(h['process']['image']['src'], h['process']['image']['alt'], '(min-width: 960px) 40vw, 100vw', ratio=(4, 5))}</div>
    </div>
    <ol class="process__list">{steps}</ol>
  </div>
</section>

<section class="section section--dark principles" aria-labelledby="principles-title">
  <div class="container">
    {section_head(h['principles']['eyebrow'], h['principles']['title'], cls='section-head--light', title_id='principles-title')}
    <ul class="principles__list">{principles}</ul>
  </div>
</section>

<section class="section faq" id="voprosy" aria-labelledby="faq-title">
  <div class="container faq__grid">
    <div>
      {section_head(h['faq']['eyebrow'], h['faq']['title'], title_id='faq-title')}
      <p class="faq__more" data-reveal>Не нашли ответ? <a href="#zayavka">Задайте вопрос в заявке</a> — ответим лично.</p>
    </div>
    <div class="faq__list" data-reveal>{faq_block(h['faq']['items'], open_first=True)}</div>
  </div>
</section>

{lead_section(ctx, 'home', 'lf-home')}
"""
    return ("/", ctx.render(path="/", title=None, overlay=True, body_class="page-home",
                            description=site["seo"]["defaultDescription"], body=body,
                            jsonld=[faq_jsonld(h["faq"]["items"])]), True)


# ── Страница направления ─────────────────────────────────────────────────
def category_page(ctx, cat):
    site = ctx.site
    path = f"/uslugi/{cat['id']}/"
    crumbs = [("Главная", "/"), ("Направления", "/#napravleniya"), (cat["title"], None)]
    projects = [p for p in ctx.projects if cat["id"] in p.get("categories", [])]
    preset = cat.get("calcPreset") or {}
    features = "".join(f"""
      <li class="feature" data-reveal><span class="feature__num">{i + 1:02d}</span>
        <h3>{esc(f['title'])}</h3><p>{esc(f['text'])}</p></li>""" for i, f in enumerate(cat.get("features", [])))
    suitable = "".join(f"<li>{esc(s)}</li>" for s in cat.get("suitableFor", []))
    desc = "".join(f"<p>{esc(p)}</p>" for p in cat.get("description", []))
    others = "".join(f'<li><a href="/uslugi/{c["id"]}/">{esc(c["title"])}{ARROW}</a></li>'
                     for c in ctx.categories if c["id"] != cat["id"])
    if projects:
        proj = f'<div class="project-grid">{"".join(project_card(p) for p in projects)}</div>'
    else:
        proj = ('<div class="empty-state"><p>Проекты этого направления скоро появятся в каталоге.</p>'
                f'{btn("Обсудить проект", "#zayavka", "outline")}</div>')
    region = site["region"]["inPhrase"] if filled(site["region"]["inPhrase"]) else ""

    body = f"""
<section class="page-hero">
  <div class="page-hero__media">{img(cat['image']['src'], cat['image']['alt'], '100vw', eager=True)}</div>
  <div class="container page-hero__inner">
    {breadcrumbs(crumbs)}
    <h1 class="page-hero__title">{esc(cat['title'])}</h1>
    <p class="page-hero__text">{esc(cat['lead'])}</p>
    <div class="hero__actions">
      {btn('Рассчитать стоимость', calc_url(preset), 'primary', arrow=True)}
      {btn('Смотреть проекты', '#proekty', 'outline-light')}
    </div>
  </div>
</section>

<section class="section" aria-labelledby="about-title">
  <div class="container about">
    <div class="about__text" data-reveal>
      <p class="eyebrow">О технологии</p>
      <h2 class="section-head__title" id="about-title">{esc((cat.get('seoTitle') or cat['title']) + (' ' + region if region else ''))}</h2>
      <div class="prose">{desc}</div>
    </div>
    {f'<aside class="about__aside" data-reveal><p class="about__aside-title">Подходит для</p><ul class="check-list">{suitable}</ul></aside>' if suitable else ''}
  </div>
</section>

{f'''<section class="section section--sand" aria-labelledby="feat-title">
  <div class="container">
    {section_head('Особенности', 'Что важно знать', title_id='feat-title')}
    <ul class="feature-list">{features}</ul>
  </div>
</section>''' if features else ''}

<section class="section" id="proekty" aria-labelledby="cat-proj-title">
  <div class="container">
    <div class="section-head-row">
      {section_head('Проекты', cat['title'], title_id='cat-proj-title')}
      {btn('Весь каталог', '/proekty/?cat=' + cat['id'], 'outline', arrow=True) if projects else ''}
    </div>
    {proj}
  </div>
</section>

{calc_band(ctx, title='Рассчитайте предварительную стоимость')}

<section class="section section--tight" aria-labelledby="others-title">
  <div class="container">
    <h2 class="small-title" id="others-title">Другие направления</h2>
    <ul class="link-list">{others}</ul>
  </div>
</section>

{lead_section(ctx, 'category:' + cat['id'], 'lf-cat', preset=preset)}
"""
    return (path, ctx.render(path=path, title=f"{cat.get('seoTitle') or cat['title']} {region}".strip(),
                             description=cat.get("seoDescription") or cat["lead"], body=body, overlay=True,
                             og_image=None, jsonld=[bc_jsonld(site, crumbs)]), True)


# ── Каталог проектов ─────────────────────────────────────────────────────
def catalog_page(ctx):
    site = ctx.site
    crumbs = [("Главная", "/"), ("Проекты", None)]
    used = [c for c in ctx.categories if any(c["id"] in p.get("categories", []) for p in ctx.projects)]
    filters = '<button type="button" class="chip" data-filter="all" aria-pressed="true">Все</button>' + "".join(
        f'<button type="button" class="chip" data-filter="{c["id"]}" aria-pressed="false">{esc(c.get("navTitle") or c["title"])}</button>'
        for c in used)
    cards = "".join(project_card(p, attrs=f' data-categories="{esc(" ".join(p.get("categories", [])))}"')
                    for p in ctx.projects)
    any_demo = any(p.get("demo") for p in ctx.projects)
    body = f"""
<section class="page-head">
  <div class="container">
    {breadcrumbs(crumbs)}
    <h1 class="page-head__title">Проекты домов и бань</h1>
    <p class="page-head__text">Каталог загородных домов, бань и построек. Выберите направление, откройте проект, чтобы посмотреть характеристики, и рассчитайте стоимость похожего строения.</p>
    {'<p class="note">Сейчас в каталоге демонстрационные карточки с фотографиями-иллюстрациями. Они показывают формат каталога и не являются объектами компании.</p>' if any_demo else ''}
  </div>
</section>
<section class="section section--flush-top" data-catalog aria-label="Каталог проектов">
  <div class="container">
    <div class="catalog-bar">
      <div class="chips" role="group" aria-label="Фильтр по направлению">{filters}</div>
      <p class="catalog-bar__count">Найдено: <b data-catalog-count>{len(ctx.projects)}</b></p>
    </div>
    <div class="project-grid">{cards}</div>
    <div class="empty-state" data-catalog-empty hidden><p>В этом направлении пока нет проектов.</p>{btn('Обсудить индивидуальный проект', '/kontakty/#zayavka', 'outline')}</div>
  </div>
</section>
{calc_band(ctx)}
"""
    return ("/proekty/", ctx.render(path="/proekty/", title="Проекты домов и бань",
                                    description="Каталог проектов загородных домов, бань и построек: площадь, этажность, технология строительства. Предварительный расчёт стоимости.",
                                    body=body, jsonld=[bc_jsonld(site, crumbs)]), True)


# ── Страница проекта ─────────────────────────────────────────────────────
def project_page(ctx, p):
    site = ctx.site
    path = f"/proekty/{p['id']}/"
    crumbs = [("Главная", "/"), ("Проекты", "/proekty/"), (p["title"], None)]
    images = p.get("images", [])
    main = images[0] if images else {"src": "", "alt": ""}
    thumbs = ""
    if len(images) > 1:
        tlist = []
        for i, im in enumerate(images):
            srcset, src = img_srcset(im["src"])
            tlist.append(
                f'<li><button type="button" class="gallery__thumb" data-gallery-thumb aria-current="{str(i == 0).lower()}"'
                f' data-srcset="{esc(srcset)}" data-src="{esc(src)}" data-alt="{esc(im["alt"])}" aria-label="Фото {i + 1}">'
                f'{img(im["src"], "", "120px")}</button></li>')
        thumbs = f'<ul class="gallery__thumbs">{"".join(tlist)}</ul>'
    specs = [("Тип строения", p.get("type")), ("Технология", p.get("technology")),
             ("Площадь", fmt_area(p.get("area"))), ("Этажность", p.get("floors")),
             ("Габариты", p.get("dimensions") if p.get("dimensions") not in ("—", "") else None)]
    specs += [(s["label"], s["value"]) for s in p.get("specs", [])]
    spec_html = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in specs if v)
    price = (f'<p class="project-price__value">{fmt_price(p["price"])}</p>'
             if isinstance(p.get("price"), (int, float)) else "")
    cats = [ctx.cat(c) for c in p.get("categories", []) if ctx.cat(c)]
    related = [q for q in ctx.projects if q["id"] != p["id"] and set(q.get("categories", [])) & set(p.get("categories", []))][:3]
    desc = "".join(f"<p>{esc(x)}</p>" for x in p.get("description", []))
    demo_note = ('<p class="note note--demo">Демонстрационная карточка: фотографии — иллюстрации, характеристики — пример заполнения. '
                 'Это не объект компании.</p>') if p.get("demo") else ""
    body = f"""
<section class="page-head page-head--project">
  <div class="container">
    {breadcrumbs(crumbs)}
    <p class="eyebrow">{esc(' · '.join(x for x in (p.get('type'), p.get('technology')) if x))} {demo_badge() if p.get('demo') else ''}</p>
    <h1 class="page-head__title">{esc(p['title'])}</h1>
    <p class="page-head__text">{esc(p.get('summary', ''))}</p>
  </div>
</section>
<section class="section section--flush-top">
  <div class="container project-layout">
    <div class="gallery" data-gallery>
      <div class="gallery__main" data-gallery-main>{img(main['src'], main['alt'], '(min-width: 1080px) 60vw, 100vw', eager=True, ratio=(3, 2))}</div>
      {thumbs}
    </div>
    <aside class="project-side">
      <dl class="spec-list">{spec_html}</dl>
      <div class="project-price">{price}<p class="project-price__note">{esc(p.get('priceNote') or '')}</p></div>
      <div class="project-side__actions">
        {btn('Рассчитать похожий', calc_url(p.get('calcPreset')), 'primary', arrow=True)}
        {btn('Обсудить проект', '#zayavka', 'outline')}
      </div>
      {demo_note}
    </aside>
  </div>
  <div class="container project-desc">
    <div class="prose">{desc}</div>
    {('<p class="project-desc__cats">Направления: ' + ', '.join(f'<a href="/uslugi/{c["id"]}/">{esc(c["title"])}</a>' for c in cats) + '</p>') if cats else ''}
  </div>
</section>
{f'''<section class="section section--sand" aria-labelledby="rel-title">
  <div class="container">
    {section_head(None, 'Похожие проекты', title_id='rel-title')}
    <div class="project-grid">{"".join(project_card(q) for q in related)}</div>
  </div>
</section>''' if related else ''}
{lead_section(ctx, 'project', 'lf-proj', project=p['title'], preset=p.get('calcPreset'), title='Обсудить этот проект', text='Оставьте контакты — уточним, подходит ли проект под ваш участок и задачи, и подготовим расчёт.')}
"""
    og = None
    first = images[0]["src"] if images else None
    if first:
        _, og = img_srcset(first)
    index = not p.get("demo")
    return (path, ctx.render(path=path, title=p["title"], description=p.get("summary") or p["title"],
                             body=body, og_image=og, noindex=not index,
                             jsonld=[bc_jsonld(site, crumbs)]), index)


# ── Калькулятор ──────────────────────────────────────────────────────────
def calculator_page(ctx):
    site, calc = ctx.site, ctx.calc
    crumbs = [("Главная", "/"), ("Калькулятор", None)]
    cost_faq = [it for it in ctx.home["faq"]["items"] if "стоимост" in it["q"].lower()]
    schema = {k: v for k, v in calc.items() if not k.startswith("_")}
    body = f"""
<section class="page-head page-head--calc">
  <div class="container">
    {breadcrumbs(crumbs)}
    <h1 class="page-head__title">{esc(calc['title'])}</h1>
    <p class="page-head__text">{esc(calc['intro'])}</p>
    <p class="note" data-calc-mode>Автоматический расчёт пока не подключён: калькулятор соберёт параметры, а стоимость рассчитает специалист. Мы не показываем примерные суммы, чтобы не вводить вас в заблуждение.</p>
  </div>
</section>
<section class="section section--flush-top">
  <div class="container">
    <div class="calc" data-calculator>
      {json_script(schema, attrs=' data-calc-schema')}
      <div class="calc-progress" data-calc-progress></div>
      <div class="calc__body">
        <form class="calc-step" data-calc-step novalidate aria-label="Параметры строительства"></form>
        <div class="calc-result" data-calc-result hidden></div>
        <aside class="calc-summary" data-calc-summary aria-label="Выбранные параметры"></aside>
      </div>
      <div class="calc-nav" data-calc-nav></div>
      <p class="visually-hidden" data-calc-live aria-live="polite"></p>
      <noscript><p class="note">Для работы калькулятора включите JavaScript или свяжитесь с нами по телефону: {esc(site['contacts']['phone'])}.</p></noscript>
    </div>
  </div>
</section>
<section class="section section--sand calc-lead" data-calc-lead hidden id="zayavka" aria-labelledby="calc-lead-title">
  <div class="container lead-section__grid">
    <div class="lead-section__intro">
      <p class="eyebrow">Заявка</p>
      <h2 class="section-head__title" id="calc-lead-title">Отправьте параметры — уточним расчёт</h2>
      <p class="section-head__text">Выбранные параметры уже прикреплены к заявке. Добавьте контакты, и мы свяжемся с вами.</p>
      <dl class="contact-list">{contact_rows(site)}</dl>
    </div>
    <div class="lead-section__form">{lead_form(ctx, calc, site, 'calculator', 'lf-calc', submit='Отправить параметры')}</div>
  </div>
</section>
<section class="section" aria-labelledby="calc-faq-title">
  <div class="container faq__grid">
    {section_head('Вопросы', 'Из чего складывается стоимость', title_id='calc-faq-title')}
    <div class="faq__list">{faq_block(cost_faq)}</div>
  </div>
</section>
"""
    return ("/kalkulyator/", ctx.render(path="/kalkulyator/", title="Калькулятор стоимости строительства дома и бани",
                                        description="Пошаговый калькулятор предварительной стоимости строительства дома, бани или загородной постройки: технология, размеры, комплектация, фундамент и кровля.",
                                        body=body, body_class="page-calc",
                                        jsonld=[bc_jsonld(site, crumbs), faq_jsonld(cost_faq)]), True)


# ── Контакты ─────────────────────────────────────────────────────────────
def contacts_page(ctx):
    site = ctx.site
    crumbs = [("Главная", "/"), ("Контакты", None)]
    body = f"""
<section class="page-head">
  <div class="container">
    {breadcrumbs(crumbs)}
    <h1 class="page-head__title">Контакты</h1>
    <p class="page-head__text">Позвоните, напишите в мессенджер или оставьте заявку — обсудим ваш дом или баню.</p>
  </div>
</section>
<section class="section section--flush-top">
  <div class="container contacts-grid">
    <div class="contact-card contact-card--main">
      <p class="eyebrow">Телефон</p>
      <p class="contact-card__big">{phone_link(site)}</p>
      <p class="eyebrow">Мессенджеры</p>
      {messengers(site, 'messengers messengers--pills')}
    </div>
    <dl class="contact-list contact-card">{contact_rows(site)}</dl>
    <div class="contact-card">
      <p class="eyebrow">География работ</p>
      <p class="contact-card__big contact-card__big--sm">{esc(site['region']['name'])}</p>
      <p>{esc(site['region'].get('note', ''))}</p>
    </div>
  </div>
</section>
{lead_section(ctx, 'contacts', 'lf-contacts')}
"""
    return ("/kontakty/", ctx.render(path="/kontakty/", title="Контакты",
                                     description="Контакты компании по строительству загородных домов и бань: телефон, мессенджеры, регион работы и форма заявки.",
                                     body=body, jsonld=[bc_jsonld(site, crumbs)]), True)


def privacy_page(ctx):
    crumbs = [("Главная", "/"), ("Политика конфиденциальности", None)]
    body = f"""
<section class="page-head">
  <div class="container narrow">
    {breadcrumbs(crumbs)}
    <h1 class="page-head__title">Политика конфиденциальности</h1>
    <div class="prose">
      <p class="note">[Заполнитель. Разместите здесь политику обработки персональных данных компании в соответствии с 152-ФЗ: оператор и его реквизиты, цели и состав обрабатываемых данных, правовые основания, сроки хранения, порядок отзыва согласия, контакты для обращений. Страница закрыта от индексации, пока текст не заполнен — уберите noindex в sitegen/pages.py.]</p>
      <p>Форма заявки на сайте собирает имя, телефон, сведения о планируемом строительстве и, если посетитель воспользовался калькулятором, выбранные в нём параметры.</p>
    </div>
  </div>
</section>"""
    return ("/politika/", ctx.render(path="/politika/", title="Политика конфиденциальности",
                                     description="Политика обработки персональных данных.", body=body, noindex=True), False)


def not_found_page(ctx):
    body = f"""
<section class="page-head page-404">
  <div class="container narrow">
    <p class="eyebrow">Ошибка 404</p>
    <h1 class="page-head__title">Страница не найдена</h1>
    <p class="page-head__text">Возможно, её перенесли или в адресе опечатка.</p>
    <div class="hero__actions">{btn('На главную', '/', 'primary')}{btn('Каталог проектов', '/proekty/', 'outline')}</div>
  </div>
</section>"""
    return ("/404.html", ctx.render(path="/404.html", title="Страница не найдена",
                                    description="Страница не найдена", body=body, noindex=True), False)
