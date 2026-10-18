import { initLeadForms } from './lead-form.js';
import { track } from './analytics.js';

const cfg = JSON.parse(document.getElementById('site-config')?.textContent || '{}');
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

// ── Шапка: фон после прокрутки ───────────────────────────────────────
const header = document.querySelector('[data-header]');
if (header) {
  const onScroll = () => header.classList.toggle('is-scrolled', scrollY > 24);
  onScroll();
  addEventListener('scroll', onScroll, { passive: true });
}

// ── Мобильное меню ──────────────────────────────────────────────────
const menuBtn = document.querySelector('[data-menu-toggle]');
const menu = document.getElementById('site-menu');
if (menuBtn && menu) {
  const setOpen = (open) => {
    menuBtn.setAttribute('aria-expanded', String(open));
    menuBtn.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    document.body.classList.toggle('menu-open', open);
  };
  menuBtn.addEventListener('click', () => setOpen(menuBtn.getAttribute('aria-expanded') !== 'true'));
  menu.addEventListener('click', (e) => { if (e.target.closest('a')) setOpen(false); });
  addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.body.classList.contains('menu-open')) { setOpen(false); menuBtn.focus(); }
  });
  matchMedia('(min-width: 1080px)').addEventListener('change', (e) => { if (e.matches) setOpen(false); });
}

// ── Появление блоков при прокрутке ──────────────────────────────────
const revealEls = document.querySelectorAll('[data-reveal]');
if (!reduceMotion && 'IntersectionObserver' in window) {
  const io = new IntersectionObserver((entries) => {
    for (const en of entries) if (en.isIntersecting) { en.target.classList.add('is-visible'); io.unobserve(en.target); }
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  revealEls.forEach((el) => { el.classList.add('reveal'); io.observe(el); });
}

// ── Фильтр каталога проектов ────────────────────────────────────────
const catalog = document.querySelector('[data-catalog]');
if (catalog) {
  const buttons = [...catalog.querySelectorAll('[data-filter]')];
  const cards = [...catalog.querySelectorAll('[data-categories]')];
  const empty = catalog.querySelector('[data-catalog-empty]');
  const count = catalog.querySelector('[data-catalog-count]');
  const apply = (cat, push) => {
    let shown = 0;
    for (const c of cards) {
      const ok = cat === 'all' || c.dataset.categories.split(' ').includes(cat);
      c.hidden = !ok;
      if (ok) shown += 1;
    }
    buttons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.filter === cat)));
    if (empty) empty.hidden = shown > 0;
    if (count) count.textContent = String(shown);
    if (push) {
      const url = new URL(location.href);
      if (cat === 'all') url.searchParams.delete('cat'); else url.searchParams.set('cat', cat);
      history.replaceState(null, '', url);
    }
  };
  buttons.forEach((b) => b.addEventListener('click', () => apply(b.dataset.filter, true)));
  const initial = new URLSearchParams(location.search).get('cat');
  apply(buttons.some((b) => b.dataset.filter === initial) ? initial : 'all', false);
}

// ── Горизонтальная лента проектов ───────────────────────────────────
document.querySelectorAll('[data-scroller]').forEach((sc) => {
  const wrap = sc.closest('section');
  const prev = wrap?.querySelector('[data-scroll-prev]');
  const next = wrap?.querySelector('[data-scroll-next]');
  if (!prev || !next) return;
  const step = () => (sc.firstElementChild?.getBoundingClientRect().width || 400) + 28;
  const update = () => {
    prev.disabled = sc.scrollLeft < 8;
    next.disabled = sc.scrollLeft + sc.clientWidth >= sc.scrollWidth - 8;
  };
  prev.addEventListener('click', () => sc.scrollBy({ left: -step(), behavior: reduceMotion ? 'auto' : 'smooth' }));
  next.addEventListener('click', () => sc.scrollBy({ left: step(), behavior: reduceMotion ? 'auto' : 'smooth' }));
  sc.addEventListener('scroll', update, { passive: true });
  addEventListener('resize', update);
  update();
});

// ── Галерея проекта ─────────────────────────────────────────────────
document.querySelectorAll('[data-gallery]').forEach((g) => {
  const main = g.querySelector('[data-gallery-main]');
  const thumbs = [...g.querySelectorAll('[data-gallery-thumb]')];
  thumbs.forEach((t) => t.addEventListener('click', () => {
    const img = main.querySelector('img');
    img.srcset = t.dataset.srcset;
    img.src = t.dataset.src;
    img.alt = t.dataset.alt;
    thumbs.forEach((x) => x.setAttribute('aria-current', String(x === t)));
  }));
});

// ── Цели: клик по телефону и мессенджерам ───────────────────────────
document.addEventListener('click', (e) => {
  const a = e.target.closest('a[href^="tel:"]');
  if (a) track('phone_click');
});

// ── Формы и калькулятор ─────────────────────────────────────────────
initLeadForms(cfg);
const calcRoot = document.querySelector('[data-calculator]');
if (calcRoot) import('./calculator/ui.js').then((m) => m.mountCalculator(calcRoot));
