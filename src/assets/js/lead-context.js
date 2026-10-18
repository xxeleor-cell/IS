/**
 * Параметры из калькулятора, которые прикрепляются к заявке.
 * Хранятся в sessionStorage, поэтому доступны на любой странице сайта
 * в пределах вкладки, пока посетитель их не уберёт или не отправит заявку.
 */
const KEY = 'lead:calc';
export const CHANGE_EVENT = 'leadcontext:change';

export function getCalcContext() {
  try { return JSON.parse(sessionStorage.getItem(KEY)); } catch { return null; }
}

export function setCalcContext(ctx) {
  try { sessionStorage.setItem(KEY, JSON.stringify({ ...ctx, savedAt: new Date().toISOString() })); } catch { /* недоступно */ }
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
}

export function clearCalcContext() {
  try { sessionStorage.removeItem(KEY); } catch { /* недоступно */ }
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
}
