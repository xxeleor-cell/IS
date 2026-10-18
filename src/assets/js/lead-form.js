/**
 * Формы заявки [data-lead-form]: проверка полей, прикрепление параметров
 * калькулятора и отправка через lead-transport.js.
 * Успех показывается только если заявка действительно принята сервером.
 */
import { sendLead } from './lead-transport.js';
import { getCalcContext, clearCalcContext, CHANGE_EVENT } from './lead-context.js';
import { track } from './analytics.js';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const digits = (s) => String(s || '').replace(/\D/g, '');

/** Российский номер приводим к виду +7 (999) 123-45-67, остальные оставляем как есть. */
export function formatPhone(raw) {
  let d = digits(raw);
  if (d.length === 11 && (d[0] === '8' || d[0] === '7')) d = d.slice(1);
  if (d.length !== 10) return String(raw).trim();
  return `+7 (${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6, 8)}-${d.slice(8)}`;
}

const RULES = {
  name: (v) => (!v.trim() ? 'Укажите имя' : v.trim().length > 80 ? 'Слишком длинное имя' : null),
  phone: (v) => {
    const n = digits(v).length;
    if (!n) return 'Укажите телефон';
    return n < 10 || n > 15 ? 'Проверьте номер телефона' : null;
  },
  message: (v) => (v.length > 2000 ? 'Не более 2000 символов' : null),
  consent: (_, el) => (el.checked ? null : 'Нужно согласие на обработку данных'),
};

function utm() {
  try {
    const q = new URLSearchParams(location.search);
    const keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'yclid'];
    const found = Object.fromEntries(keys.filter((k) => q.get(k)).map((k) => [k, q.get(k)]));
    if (Object.keys(found).length) sessionStorage.setItem('lead:utm', JSON.stringify(found));
    return JSON.parse(sessionStorage.getItem('lead:utm')) || {};
  } catch { return {}; }
}

function contactsHTML(cfg) {
  const c = cfg.contacts || {};
  const parts = [];
  if (c.phoneHref) parts.push(`<a href="tel:${esc(c.phoneHref)}">${esc(c.phone)}</a>`);
  for (const m of c.messengers || []) if (m.url) parts.push(`<a href="${esc(m.url)}" target="_blank" rel="noopener">${esc(m.label)}</a>`);
  return parts.length ? `<p class="lead-status__contacts">${parts.join(' · ')}</p>` : '';
}

function enhance(form, cfg) {
  const statusEl = form.querySelector('[data-lead-status]');
  const calcEl = form.querySelector('[data-lead-calc]');
  const submitBtn = form.querySelector('[type="submit"]');
  let lastPayloadText = '';

  function setError(name, msg) {
    const input = form.elements[name];
    if (!input) return;
    const wrap = input.closest('.field');
    const p = wrap?.querySelector('.field__error');
    wrap?.classList.toggle('is-invalid', !!msg);
    if (msg) input.setAttribute('aria-invalid', 'true'); else input.removeAttribute('aria-invalid');
    if (p) { p.textContent = msg || ''; p.hidden = !msg; }
  }

  function validate() {
    let first = null;
    for (const [name, rule] of Object.entries(RULES)) {
      const el = form.elements[name];
      if (!el) continue;
      const msg = rule(el.value || '', el);
      setError(name, msg);
      if (msg && !first) first = el;
    }
    return first;
  }

  // Прикреплённые параметры калькулятора
  function renderCalc() {
    if (!calcEl) return;
    const ctx = getCalcContext();
    if (!ctx?.summary) { calcEl.hidden = true; calcEl.innerHTML = ''; return; }
    const rows = ctx.summary.flatMap((g) => g.items)
      .map((i) => `<li><span>${esc(i.label)}</span><b>${esc(i.value)}</b></li>`).join('');
    calcEl.hidden = false;
    calcEl.innerHTML = `<div class="lead-calc__head"><p>Параметры из калькулятора прикреплены к заявке</p>
      <button type="button" class="link-btn" data-lead-calc-remove>Убрать</button></div><ul class="lead-calc__list">${rows}</ul>`;
    // Подставляем тип строения и технологию, если посетитель их ещё не выбрал
    for (const key of ['buildingType', 'technology']) {
      const sel = form.elements[key];
      const val = ctx.params?.[key];
      if (sel && !sel.value && val && [...sel.options].some((o) => o.value === val)) sel.value = val;
    }
  }
  renderCalc();
  window.addEventListener(CHANGE_EVENT, renderCalc);
  calcEl?.addEventListener('click', (e) => {
    if (e.target.closest('[data-lead-calc-remove]')) clearCalcContext();
  });

  form.elements.phone?.addEventListener('blur', (e) => { e.target.value = formatPhone(e.target.value); });
  form.addEventListener('input', (e) => {
    if (e.target.closest('.field.is-invalid')) {
      const rule = RULES[e.target.name];
      if (rule) setError(e.target.name, rule(e.target.value || '', e.target));
    }
  });
  form.addEventListener('change', (e) => {
    if (e.target.name === 'consent') setError('consent', RULES.consent('', e.target));
  });

  function showStatus(kind, html) {
    statusEl.className = `lead-status lead-status--${kind}`;
    statusEl.innerHTML = html;
    statusEl.hidden = false;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (form.dataset.busy) return;
    const invalid = validate();
    if (invalid) { invalid.focus(); return; }
    if (form.elements.website?.value) return; // honeypot: бот

    const sel = (name) => {
      const el = form.elements[name];
      return el ? { value: el.value || null, label: el.value ? el.selectedOptions?.[0]?.text : null } : null;
    };
    const ctx = getCalcContext();
    const payload = {
      name: form.elements.name.value.trim(),
      phone: formatPhone(form.elements.phone.value),
      buildingType: sel('buildingType'),
      technology: sel('technology'),
      message: form.elements.message?.value.trim() || '',
      project: form.elements.project?.value || null,
      source: form.elements.source?.value || null,
      calculator: ctx ? { params: ctx.params, summaryText: ctx.summaryText, result: ctx.result } : null,
      page: location.pathname,
      utm: utm(),
      sentAt: new Date().toISOString(),
    };
    lastPayloadText = [
      `Имя: ${payload.name}`, `Телефон: ${payload.phone}`,
      payload.buildingType?.label && `Тип строения: ${payload.buildingType.label}`,
      payload.technology?.label && `Технология: ${payload.technology.label}`,
      payload.project && `Проект: ${payload.project}`,
      payload.message && `Пожелания: ${payload.message}`,
      ctx?.summaryText && `\nПараметры из калькулятора:\n${ctx.summaryText}`,
    ].filter(Boolean).join('\n');

    form.dataset.busy = '1';
    submitBtn.disabled = true;
    submitBtn.classList.add('is-loading');
    statusEl.hidden = true;
    const res = await sendLead(payload, cfg.leads);
    delete form.dataset.busy;
    submitBtn.disabled = false;
    submitBtn.classList.remove('is-loading');

    if (res.ok) {
      track('lead_submit', { source: payload.source });
      form.reset();
      clearCalcContext();
      showStatus('ok', '<p><b>Заявка отправлена.</b> Мы свяжемся с вами, чтобы уточнить детали.</p>');
      return;
    }
    track('lead_error', { reason: res.reason });
    const copyBtn = navigator.clipboard ? '<button type="button" class="link-btn" data-lead-copy>Скопировать текст заявки</button>' : '';
    const head = res.reason === 'not_configured'
      ? '<p><b>Заявка не отправлена:</b> онлайн-отправка на сайте пока не подключена. Пожалуйста, свяжитесь с нами по телефону или в мессенджере — текст заявки можно скопировать.</p>'
      : '<p><b>Не удалось отправить заявку.</b> Проверьте подключение к интернету и попробуйте ещё раз или свяжитесь с нами напрямую.</p>';
    showStatus('error', head + contactsHTML(cfg) + copyBtn);
  });

  statusEl.addEventListener('click', async (e) => {
    if (!e.target.closest('[data-lead-copy]')) return;
    try {
      await navigator.clipboard.writeText(lastPayloadText);
      e.target.textContent = 'Текст скопирован';
    } catch {
      e.target.textContent = 'Не удалось скопировать';
    }
  });
}

export function initLeadForms(cfg) {
  document.querySelectorAll('[data-lead-form]').forEach((f) => enhance(f, cfg));
}
