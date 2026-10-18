/**
 * Тесты калькулятора. Работают и в браузере (tests/index.html), и в Node (tests/run.mjs).
 *  1. Логика анкеты (engine.js) — фиксированные проверки.
 *  2. Контрольные примеры формулы (tests/pricing-cases.json) — заполняются
 *     примерами заказчика: ответы анкеты → ожидаемый результат.
 */
import * as E from '../src/assets/js/calculator/engine.js';
import { calculate, FORMULA } from '../src/assets/js/calculator/pricing.js';

function check(name, fn) {
  try {
    const msg = fn();
    return { name, ok: msg === true || msg === undefined, detail: msg === true ? '' : msg || '' };
  } catch (err) {
    return { name, ok: false, detail: String(err && err.stack || err) };
  }
}
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b) || `ожидалось ${JSON.stringify(b)}, получено ${JSON.stringify(a)}`;

export function engineTests(schema) {
  const field = (id) => schema.steps.flatMap((s) => s.fields).find((f) => f.id === id);
  return [
    check('parseNumber понимает запятую и пробелы', () => eq([E.parseNumber('120,5'), E.parseNumber(' 1 000 '), Number.isNaN(E.parseNumber('12a'))], [120.5, 1000, true])),
    check('обязательное поле без ответа — ошибка', () => eq(E.validateField(field('buildingType'), undefined), 'Выберите вариант')),
    check('число вне диапазона — ошибка', () => eq(E.validateField(field('area'), '3'), 'Минимум 6 м²')),
    check('число в диапазоне — без ошибки', () => eq(E.validateField(field('area'), '120'), null)),
    check('вариант, недоступный для ответа, отклоняется', () => eq(E.validateField(field('buildingType'), 'castle', {}), 'Выберите вариант')),
    check('скрытые поля не попадают в параметры', () => {
      const p = E.toParams(schema, { buildingType: 'house', sizeMode: 'area', area: '100', length: '10', width: '8' });
      return eq([p.area, 'length' in p, 'otherKind' in p], [100, false, false]);
    }),
    check('смена типа строения убирает недоступные доп. работы', () => {
      const st = E.prune(schema, { buildingType: 'house', extras: ['stove', 'fireplace', 'terrace'] });
      return eq(st.extras, ['fireplace', 'terrace']);
    }),
    check('площадь из длины и ширины НЕ вычисляется движком', () => {
      const p = E.toParams(schema, { sizeMode: 'dims', length: '10', width: '8' });
      return eq([p.length, p.width, 'area' in p], [10, 8, false]);
    }),
    check('пресет из адреса принимает только допустимые значения', () =>
      eq(E.stateFromQuery(schema, '?buildingType=banya&technology=steel&floors=2&evil=1'), { buildingType: 'banya', floors: '2' })),
    check('пока формула не подключена — сумма не возвращается', () => {
      if (FORMULA.status === 'ready') return true;
      const r = calculate({ buildingType: 'house', area: 100 });
      return eq([r.status, 'total' in r], ['not_configured', false]);
    }),
  ];
}

export function pricingTests(schema, data) {
  return (data.cases || []).map((c) => check(`пример: ${c.name}`, () => {
    const params = c.params || E.toParams(schema, { ...E.defaults(schema), ...c.answers });
    if (c.answers) {
      const bad = E.firstInvalidStep(schema, E.prune(schema, { ...E.defaults(schema), ...c.answers }));
      if (bad !== -1) return `ответы не проходят проверку анкеты (шаг ${bad + 1})`;
    }
    const r = calculate(params);
    const exp = c.expect || {};
    if (exp.status && r.status !== exp.status) return `статус: ожидалось ${exp.status}, получено ${r.status}`;
    if ('total' in exp && r.total !== exp.total) return `итог: ожидалось ${exp.total}, получено ${r.total}`;
    if (exp.breakdown) {
      for (const b of exp.breakdown) {
        const got = (r.breakdown || []).find((x) => x.id === b.id);
        if (!got || got.amount !== b.amount) return `строка ${b.id}: ожидалось ${b.amount}, получено ${got && got.amount}`;
      }
    }
    return true;
  }));
}
