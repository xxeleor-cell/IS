/**
 * Доставка заявок. Способ задаётся в content/site.json → leads.
 *
 *   transport: "none" — отправка не подключена. Возвращаем
 *              { ok: false, reason: 'not_configured' }: форма сообщит
 *              об этом честно и предложит связаться напрямую.
 *   transport: "http" — POST JSON на leads.endpoint. Успех — только
 *              ответ 2xx с телом { "ok": true }.
 *
 * Чтобы добавить другой канал (CRM, Bitrix24, amoCRM и т. п.), допишите
 * функцию в TRANSPORTS. Секретные токены не должны попадать в браузер —
 * отправляйте через свой сервер (пример: integrations/lead-handler.php).
 */

async function httpTransport(payload, cfg) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), cfg.timeoutMs || 12000);
  try {
    const res = await fetch(cfg.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
    let body = null;
    try { body = await res.json(); } catch { /* не JSON */ }
    if (res.ok && body && body.ok === true) return { ok: true };
    return { ok: false, reason: 'server', message: body?.error };
  } catch (err) {
    return { ok: false, reason: err.name === 'AbortError' ? 'timeout' : 'network' };
  } finally {
    clearTimeout(timer);
  }
}

const TRANSPORTS = {
  none: async () => ({ ok: false, reason: 'not_configured' }),
  http: httpTransport,
};

export function sendLead(payload, cfg = {}) {
  const fn = TRANSPORTS[cfg.transport] || TRANSPORTS.none;
  return fn(payload, cfg);
}
