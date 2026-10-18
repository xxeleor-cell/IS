/**
 * Модуль расчёта стоимости — ЕДИНСТВЕННОЕ место, где считаются деньги.
 *
 * Сейчас формула НЕ подключена: calculate() всегда возвращает
 * { status: 'not_configured' }, и интерфейс не показывает никаких сумм.
 * Здесь намеренно нет цен, ставок и коэффициентов.
 *
 * Как подключить формулу заказчика:
 *  1. Реализуйте её в calculate() буквально — со всеми условиями,
 *     коэффициентами, ограничениями и правилами округления.
 *  2. Поставьте FORMULA.status = 'ready' и укажите version.
 *  3. Внесите контрольные примеры в tests/pricing-cases.json
 *     и прогоните tests/index.html (или `node tests/run.mjs`).
 *
 * Модуль не зависит от DOM и может выполняться в браузере и в Node.
 *
 * ── Вход ────────────────────────────────────────────────────────────
 * params — результат engine.toParams(): только видимые поля анкеты.
 *   buildingType  'house' | 'banya' | 'other'
 *   otherKind     'guest' | 'utility' | 'workshop' | 'gazebo' | 'other' | (нет поля)
 *   technology    'frame' | 'beam' | 'log' | 'other' | 'consult'
 *   sizeMode      'area' | 'dims'
 *   area          number (м²)      — если sizeMode = 'area'
 *   length, width number (м)       — если sizeMode = 'dims'
 *   floors        '1' | '1.5' | '2'
 *   package       'shell' | 'warm' | 'turnkey' | 'undecided'
 *   foundation    'piles' | 'strip' | 'slab' | 'existing' | 'unknown'
 *   roof          'gable' | 'shed' | 'hip' | 'complex' | 'unknown'
 *   extras        string[]  ('terrace', 'engineering', 'interior', 'stove', 'fireplace', 'design')
 *   terraceArea   number | null
 *   location      string | null
 * Набор полей предварительный: после получения формулы схема
 * (content/calculator.json) и этот список будут приведены в соответствие.
 *
 * ── Выход (CalcResult) ──────────────────────────────────────────────
 *   { status: 'not_configured' }
 *       формула не подключена — сумма не показывается.
 *   { status: 'ok', total, currency: 'RUB', breakdown?: [{ id, label, amount }],
 *     notes?: string[], formulaVersion }
 *       предварительная стоимость; total уже округлён по правилам формулы.
 *   { status: 'needs_manual', reason }
 *       сочетание параметров, которое формула не покрывает
 *       (например, «Нужна консультация» по технологии) — расчёт вручную.
 *   { status: 'invalid', errors: { [paramId]: string } }
 *       параметры вне допустимых формулой границ.
 */

export const FORMULA = {
  status: 'not_configured', // 'ready' — после реализации формулы
  version: null, // например, 'v1 от 2026-11-01'
  currency: 'RUB',
};

export const isFormulaReady = () => FORMULA.status === 'ready';

/**
 * @param {Record<string, any>} params
 * @returns {{status: string, [k: string]: any}}
 */
export function calculate(params) {
  if (!isFormulaReady()) return { status: 'not_configured' };

  // ── Место для формулы заказчика ───────────────────────────────────
  // Пока формула не реализована, ветка недостижима (status !== 'ready').
  void params;
  return { status: 'not_configured' };
}

/** Форматирование суммы для интерфейса: «1 234 567 ₽». */
export function formatMoney(amount, currency = FORMULA.currency) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}
