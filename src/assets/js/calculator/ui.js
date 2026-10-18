/**
 * Интерфейс пошагового калькулятора. Отвечает только за отображение
 * и взаимодействие: логика анкеты — engine.js, расчёт — pricing.js.
 */
import * as E from './engine.js';
import { calculate, formatMoney, isFormulaReady, FORMULA } from './pricing.js';
import { setCalcContext } from '../lead-context.js';
import { track } from '../analytics.js';

const STORE_KEY = 'calc:v1';
// Базовый путь сайта (например, /IS при размещении на GitHub Pages)
const BASE = (() => { try { return JSON.parse(document.getElementById('site-config').textContent).base || ''; } catch { return ''; } })();
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const load = () => { try { return JSON.parse(sessionStorage.getItem(STORE_KEY)) || null; } catch { return null; } };
const save = (data) => { try { sessionStorage.setItem(STORE_KEY, JSON.stringify(data)); } catch { /* приватный режим */ } };

export function mountCalculator(root) {
  const schema = JSON.parse(root.querySelector('[data-calc-schema]').textContent);
  const els = {
    progress: root.querySelector('[data-calc-progress]'),
    step: root.querySelector('[data-calc-step]'),
    summary: root.querySelector('[data-calc-summary]'),
    nav: root.querySelector('[data-calc-nav]'),
    result: root.querySelector('[data-calc-result]'),
    live: root.querySelector('[data-calc-live]'),
    lead: document.querySelector('[data-calc-lead]'),
  };

  // ── Начальное состояние: сохранённое → пресет из адреса ─────────────
  const preset = E.stateFromQuery(schema, location.search);
  const saved = load();
  let state;
  let current = 0;
  let maxReached = 0;
  if (Object.keys(preset).length) {
    state = E.prune(schema, { ...E.defaults(schema), ...preset });
    // Начинаем с первого шага, на который ещё нет ответа.
    const firstOpen = E.firstInvalidStep(schema, state);
    current = maxReached = firstOpen === -1 ? 0 : firstOpen;
    history.replaceState(null, '', location.pathname + location.hash);
  } else if (saved?.state) {
    state = E.prune(schema, saved.state);
    current = saved.current || 0;
    maxReached = saved.maxReached || 0;
  } else {
    state = E.defaults(schema);
  }
  let showErrors = false;
  let started = false;

  const steps = () => E.visibleSteps(schema, state);
  const resultIndex = () => steps().length;
  const persist = () => save({ state, current, maxReached });

  /** Можно ли перейти к шагу i: все предыдущие шаги заполнены верно. */
  const canGoTo = (i) => {
    const bad = E.firstInvalidStep(schema, state);
    return i <= maxReached && (bad === -1 || i <= bad);
  };

  // ── Прогресс ───────────────────────────────────────────────────────
  function renderProgress() {
    const list = steps();
    const total = list.length;
    const pos = Math.min(current, total);
    const title = current >= total ? 'Результат' : list[current].title;
    const items = [...list.map((s) => s.title), 'Результат'].map((t, i) => {
      const cls = i === current ? 'is-current' : i < current || (i <= maxReached && canGoTo(i)) ? 'is-done' : '';
      const enabled = i !== current && canGoTo(i);
      return `<li class="calc-progress__item ${cls}">
        <button type="button" data-goto="${i}" ${enabled ? '' : 'disabled'} ${i === current ? 'aria-current="step"' : ''}>
          <span class="calc-progress__num">${i < total ? i + 1 : '✓'}</span>
          <span class="calc-progress__label">${esc(t)}</span>
        </button></li>`;
    }).join('');
    els.progress.innerHTML = `
      <div class="calc-progress__compact" aria-hidden="true">
        <span>${pos < total ? `Шаг ${pos + 1} из ${total}` : 'Готово'}</span><b>${esc(title)}</b>
      </div>
      <div class="calc-progress__bar" aria-hidden="true"><span style="width:${(pos / total) * 100}%"></span></div>
      <ol class="calc-progress__list">${items}</ol>`;
  }

  // ── Поля ───────────────────────────────────────────────────────────
  function fieldHTML(f) {
    const v = state[f.id];
    const err = showErrors ? E.validateField(f, v, state) : null;
    const errId = `calc-err-${f.id}`;
    const hintId = `calc-hint-${f.id}`;
    const describedBy = [f.hint ? hintId : '', err ? errId : ''].filter(Boolean).join(' ');
    const hint = f.hint ? `<p class="field__hint" id="${hintId}">${esc(f.hint)}</p>` : '';
    const error = `<p class="field__error" id="${errId}" ${err ? '' : 'hidden'}>${esc(err || '')}</p>`;
    const req = f.required ? '' : ' <span class="field__optional">необязательно</span>';

    if (f.type === 'number' || f.type === 'text') {
      const attrs = f.type === 'number'
        ? `inputmode="decimal" autocomplete="off"`
        : `autocomplete="off" ${f.maxLength ? `maxlength="${f.maxLength}"` : ''}`;
      return `<div class="field ${f.half ? 'field--half' : ''} ${err ? 'is-invalid' : ''}" data-field="${f.id}">
        <label class="field__label" for="calc-${f.id}">${esc(f.label)}${req}</label>
        <div class="input-wrap">
          <input class="input" id="calc-${f.id}" name="${f.id}" type="text" ${attrs}
            value="${esc(v ?? '')}" placeholder="${esc(f.placeholder || '')}"
            ${f.required ? 'aria-required="true"' : ''} ${err ? 'aria-invalid="true"' : ''}
            ${describedBy ? `aria-describedby="${describedBy}"` : ''}>
          ${f.unit ? `<span class="input-wrap__unit">${esc(f.unit)}</span>` : ''}
        </div>${hint}${error}</div>`;
    }

    const multi = f.type === 'multi';
    const opts = E.visibleOptions(f, state).map((o) => {
      const checked = multi ? Array.isArray(v) && v.includes(o.value) : v === o.value;
      const img = o.image
        ? `<img class="choice__img" src="${BASE}/assets/img/${esc(o.image)}-640.webp" alt="" loading="lazy" width="640" height="427">`
        : '';
      return `<label class="choice choice--${f.type} ${checked ? 'is-checked' : ''}">
        <input type="${multi ? 'checkbox' : 'radio'}" name="${f.id}" value="${esc(o.value)}" ${checked ? 'checked' : ''}>
        ${img}<span class="choice__body"><span class="choice__label">${esc(o.label)}</span>
        ${o.hint ? `<span class="choice__hint">${esc(o.hint)}</span>` : ''}</span>
        <span class="choice__mark" aria-hidden="true"></span></label>`;
    }).join('');
    return `<fieldset class="field ${err ? 'is-invalid' : ''}" data-field="${f.id}"
        ${describedBy ? `aria-describedby="${describedBy}"` : ''} ${err ? 'aria-invalid="true"' : ''}>
      <legend class="field__label">${esc(f.label)}${req}</legend>${hint}
      <div class="choices choices--${f.type}">${opts}</div>${error}</fieldset>`;
  }

  function renderStep() {
    const list = steps();
    if (current >= list.length) { els.step.hidden = true; return; }
    els.step.hidden = false;
    const s = list[current];
    els.step.innerHTML = `<h2 class="calc-step__title" tabindex="-1">${esc(s.title)}</h2>
      <div class="calc-step__fields">${E.visibleFields(s, state).map(fieldHTML).join('')}</div>`;
  }

  // ── Сводка выбранных параметров ─────────────────────────────────────
  function summaryHTML(withEdit) {
    // Показываем только шаги, до которых посетитель уже дошёл (без значений по умолчанию впереди).
    const reached = new Set(steps().slice(0, maxReached + 1).map((s) => s.id));
    const groups = E.summarize(schema, state).filter((g) => g.items.length && reached.has(g.stepId));
    if (!groups.length) return '<p class="calc-summary__empty">Здесь появятся выбранные параметры.</p>';
    const idx = (id) => steps().findIndex((s) => s.id === id);
    return `<dl class="calc-summary__list">${groups.map((g) => g.items.map((it, k) => `
      <div class="calc-summary__row"><dt>${esc(it.label)}</dt><dd>${esc(it.value)}</dd>
      ${withEdit && k === 0 && canGoTo(idx(g.stepId)) ? `<button type="button" class="link-btn" data-goto="${idx(g.stepId)}" aria-label="Изменить: ${esc(g.stepTitle)}">Изменить</button>` : ''}
      </div>`).join('')).join('')}</dl>`;
  }

  function renderSummary() {
    els.summary.innerHTML = `<details class="calc-summary__box" ${matchMedia('(min-width: 960px)').matches ? 'open' : ''}>
      <summary class="calc-summary__head">Ваши параметры</summary>${summaryHTML(true)}</details>`;
  }

  // ── Навигация ──────────────────────────────────────────────────────
  function renderNav() {
    const last = steps().length - 1;
    if (current > last) {
      els.nav.innerHTML = `<button type="button" class="btn btn--ghost" data-action="back">Изменить параметры</button>
        <button type="button" class="link-btn" data-action="reset">Начать заново</button>`;
      return;
    }
    els.nav.innerHTML = `
      ${current > 0 ? '<button type="button" class="btn btn--ghost" data-action="back">Назад</button>' : '<span></span>'}
      <button type="button" class="btn btn--primary" data-action="next">${current === last ? 'Показать результат' : 'Далее'}</button>`;
  }

  // ── Результат ──────────────────────────────────────────────────────
  function resultHTML(res) {
    if (res.status === 'ok') {
      const rows = (res.breakdown || []).map((b) =>
        `<tr><th scope="row">${esc(b.label)}</th><td>${formatMoney(b.amount, res.currency)}</td></tr>`).join('');
      return `<div class="calc-result__card is-ok">
        <p class="eyebrow">Предварительная стоимость</p>
        <p class="calc-result__total">${formatMoney(res.total, res.currency)}</p>
        ${rows ? `<table class="calc-result__table">${rows}</table>` : ''}
        ${(res.notes || []).map((n) => `<p class="calc-result__note">${esc(n)}</p>`).join('')}
        <p class="calc-result__disclaimer">Расчёт предварительный и не является публичной офертой. Точная стоимость определяется после уточнения проекта и состава работ.</p>
      </div>`;
    }
    if (res.status === 'needs_manual') {
      return `<div class="calc-result__card">
        <p class="eyebrow">Нужен индивидуальный расчёт</p>
        <h2 class="calc-result__title">Рассчитаем стоимость вручную</h2>
        <p>${esc(res.reason || 'Для выбранных параметров стоимость рассчитывается специалистом.')}</p></div>`;
    }
    if (res.status === 'invalid') {
      return `<div class="calc-result__card">
        <p class="eyebrow">Проверьте параметры</p>
        <ul>${Object.values(res.errors || {}).map((e) => `<li>${esc(e)}</li>`).join('')}</ul></div>`;
    }
    return `<div class="calc-result__card is-pending">
      <p class="eyebrow">Расчёт готовится</p>
      <h2 class="calc-result__title">Параметры собраны — стоимость рассчитает специалист</h2>
      <p>Автоматический расчёт пока не подключён, поэтому мы не показываем сумму — чтобы не вводить вас в заблуждение примерными цифрами. Отправьте заявку с выбранными параметрами, и мы подготовим предварительный расчёт.</p>
    </div>`;
  }

  function renderResult() {
    const atResult = current >= steps().length;
    els.result.hidden = !atResult;
    if (els.lead) els.lead.hidden = !atResult;
    if (!atResult) return;
    const params = E.toParams(schema, state);
    const res = calculate(params);
    els.result.innerHTML = `${resultHTML(res)}
      <div class="calc-result__summary"><h3>Выбранные параметры</h3>${summaryHTML(true)}</div>`;
    const summary = E.summarize(schema, state);
    setCalcContext({
      params,
      summary,
      summaryText: E.summaryText(summary),
      result: res.status === 'ok'
        ? { status: 'ok', total: res.total, currency: res.currency, formulaVersion: FORMULA.version }
        : { status: res.status },
    });
    track('calc_complete', { status: res.status });
  }

  function render({ focus = false } = {}) {
    renderProgress();
    renderStep();
    renderSummary();
    renderNav();
    renderResult();
    root.classList.toggle('is-result', current >= steps().length);
    persist();
    if (focus) {
      const heading = current >= steps().length
        ? els.result.querySelector('.calc-result__title, .calc-result__total, .eyebrow')
        : els.step.querySelector('.calc-step__title');
      const top = root.getBoundingClientRect().top;
      if (top < 0 || top > innerHeight * 0.4) root.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
      if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true }); }
      const label = current >= steps().length ? 'Результат' : `Шаг ${current + 1} из ${steps().length}: ${steps()[current].title}`;
      els.live.textContent = label;
    }
  }

  function goTo(i) {
    current = Math.max(0, Math.min(i, resultIndex()));
    maxReached = Math.max(maxReached, current);
    showErrors = false;
    render({ focus: true });
  }

  function next() {
    const s = steps()[current];
    const errors = E.validateStep(s, state);
    if (Object.keys(errors).length) {
      showErrors = true;
      renderStep();
      const first = els.step.querySelector('.is-invalid input, .is-invalid');
      first?.focus?.();
      els.live.textContent = 'Проверьте отмеченные поля';
      return;
    }
    goTo(current + 1);
  }

  // ── События ────────────────────────────────────────────────────────
  function onChange(e) {
    const input = e.target;
    if (!input.name) return;
    if (!started) { started = true; track('calc_start'); }
    const field = steps()[current]?.fields.find((f) => f.id === input.name);
    if (!field) return;
    if (field.type === 'multi') {
      const vals = [...els.step.querySelectorAll(`input[name="${input.name}"]:checked`)].map((i) => i.value);
      state = { ...state, [field.id]: vals };
    } else {
      state = { ...state, [field.id]: input.value };
    }
    state = E.prune(schema, state);
    // Текстовые поля не перерисовываем, чтобы не сбивать курсор.
    const isChoice = input.type === 'radio' || input.type === 'checkbox';
    if (isChoice) {
      renderStep();
      els.step.querySelector(`input[name="${CSS.escape(input.name)}"][value="${CSS.escape(input.value)}"]`)?.focus();
    } else if (showErrors) {
      const wrap = input.closest('.field');
      const err = E.validateField(field, state[field.id], state);
      wrap.classList.toggle('is-invalid', !!err);
      const p = wrap.querySelector('.field__error');
      p.hidden = !err; p.textContent = err || '';
      if (err) input.setAttribute('aria-invalid', 'true'); else input.removeAttribute('aria-invalid');
    }
    renderSummary();
    renderProgress();
    persist();
  }

  els.step.addEventListener('change', onChange);
  els.step.addEventListener('input', (e) => { if (e.target.type === 'text') onChange(e); });
  els.step.addEventListener('submit', (e) => { e.preventDefault(); next(); });
  els.step.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.type === 'text') { e.preventDefault(); next(); }
  });
  root.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn || !root.contains(btn)) return;
    if (btn.dataset.goto != null) goTo(Number(btn.dataset.goto));
    else if (btn.dataset.action === 'next') next();
    else if (btn.dataset.action === 'back') goTo(Math.min(current, resultIndex()) - 1);
    else if (btn.dataset.action === 'reset') {
      state = E.defaults(schema); maxReached = 0; started = false; goTo(0);
    }
  });

  root.classList.add('is-ready');
  root.querySelector('[data-calc-mode]')?.toggleAttribute('hidden', isFormulaReady());
  render();
}
