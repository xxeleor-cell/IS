/**
 * Цели Яндекс Метрики. Если счётчик не подключён (content/site.json →
 * analytics.yandexMetrikaId пуст), вызовы ничего не делают.
 */
export function track(goal, params) {
  const id = window.__ymId;
  if (!id || typeof window.ym !== 'function') return;
  try { window.ym(id, 'reachGoal', goal, params); } catch { /* не мешаем работе сайта */ }
}
