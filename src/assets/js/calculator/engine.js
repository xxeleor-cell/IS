/**
 * Логика анкеты калькулятора: видимость шагов и полей, валидация,
 * нормализация ответов в параметры расчёта и текстовая сводка.
 *
 * Модуль не знает ни о DOM, ни о ценах. Схема — content/calculator.json.
 * Состояние (state) — плоский объект { [fieldId]: значение } в том виде,
 * как его ввёл пользователь (числа — строками, multi — массивом).
 */

/** Выполняется ли условие showIf для текущих ответов. */
export function matches(cond, state) {
  if (!cond) return true;
  const v = state[cond.field];
  if ('eq' in cond) return v === cond.eq;
  if ('in' in cond) return cond.in.includes(v);
  if ('has' in cond) return Array.isArray(v) && v.includes(cond.has);
  return true;
}

export const visibleOptions = (field, state) =>
  (field.options || []).filter((o) => matches(o.showIf, state));

export const visibleFields = (step, state) =>
  step.fields.filter((f) => matches(f.showIf, state));

export const visibleSteps = (schema, state) =>
  schema.steps.filter((s) => visibleFields(s, state).length > 0);

/** Число из строки пользователя: допускает запятую и пробелы. NaN, если не число. */
export function parseNumber(raw) {
  if (typeof raw === 'number') return raw;
  if (raw == null) return NaN;
  const s = String(raw).replace(/\s+/g, '').replace(',', '.');
  if (s === '' || !/^-?\d*\.?\d+$/.test(s)) return NaN;
  return Number(s);
}

const isEmpty = (v) => v == null || v === '' || (Array.isArray(v) && v.length === 0);

const fmtNum = (n) => String(n).replace('.', ',');

/** Текст ошибки для поля или null. */
export function validateField(field, value, state = {}) {
  if (isEmpty(value)) {
    if (!field.required) return null;
    return field.type === 'number' || field.type === 'text'
      ? 'Заполните поле'
      : 'Выберите вариант';
  }
  if (field.type === 'number') {
    const n = parseNumber(value);
    const unit = field.unit ? ` ${field.unit}` : '';
    if (Number.isNaN(n)) return 'Введите число';
    if (field.min != null && n < field.min) return `Минимум ${fmtNum(field.min)}${unit}`;
    if (field.max != null && n > field.max) return `Максимум ${fmtNum(field.max)}${unit}`;
  }
  if (field.type === 'text' && field.maxLength && String(value).length > field.maxLength) {
    return `Не более ${field.maxLength} символов`;
  }
  if (field.type === 'cards' || field.type === 'segmented') {
    if (!visibleOptions(field, state).some((o) => o.value === value)) return 'Выберите вариант';
  }
  return null;
}

/** Ошибки видимых полей шага: { fieldId: текст }. Пустой объект — шаг заполнен верно. */
export function validateStep(step, state) {
  const errors = {};
  for (const f of visibleFields(step, state)) {
    const err = validateField(f, state[f.id], state);
    if (err) errors[f.id] = err;
  }
  return errors;
}

/** Индекс первого шага с ошибками или -1. */
export function firstInvalidStep(schema, state) {
  return visibleSteps(schema, state).findIndex(
    (s) => Object.keys(validateStep(s, state)).length > 0,
  );
}

/** Значения по умолчанию из схемы (field.default). */
export function defaults(schema) {
  const st = {};
  for (const s of schema.steps) for (const f of s.fields) if ('default' in f) st[f.id] = f.default;
  return st;
}

/**
 * Удаляет ответы на скрытые поля и скрытые варианты multi.
 * Нужен после каждого изменения: например, при смене типа строения
 * отметка «Печь и дымоход» у дома должна исчезнуть.
 */
export function prune(schema, state) {
  const out = { ...state };
  let changed = true;
  // Повторяем, пока есть изменения: скрытие одного поля может скрыть другое.
  while (changed) {
    changed = false;
    for (const s of schema.steps) {
      for (const f of s.fields) {
        if (!(f.id in out)) continue;
        if (!matches(f.showIf, out)) { delete out[f.id]; changed = true; continue; }
        if (f.type === 'multi' && Array.isArray(out[f.id])) {
          const allowed = visibleOptions(f, out).map((o) => o.value);
          const kept = out[f.id].filter((v) => allowed.includes(v));
          if (kept.length !== out[f.id].length) { out[f.id] = kept; changed = true; }
        }
      }
    }
  }
  return out;
}

/**
 * Параметры для модуля расчёта: только видимые поля, числа — числами,
 * пустые необязательные поля — null. Ничего не вычисляет (например,
 * площадь из длины и ширины не считается — это решает формула).
 */
export function toParams(schema, state) {
  const clean = prune(schema, state);
  const params = {};
  for (const s of visibleSteps(schema, clean)) {
    for (const f of visibleFields(s, clean)) {
      const v = clean[f.id];
      if (f.type === 'number') params[f.id] = isEmpty(v) ? null : parseNumber(v);
      else if (f.type === 'multi') params[f.id] = Array.isArray(v) ? [...v] : [];
      else params[f.id] = isEmpty(v) ? null : v;
    }
  }
  return params;
}

/** Человекочитаемое значение поля. */
export function displayValue(field, value) {
  if (isEmpty(value)) return '—';
  const opt = (v) => (field.options || []).find((o) => o.value === v)?.label ?? v;
  if (field.type === 'multi') return value.map(opt).join(', ');
  if (field.type === 'number') return `${fmtNum(parseNumber(value))}${field.unit ? ` ${field.unit}` : ''}`;
  if (field.type === 'cards' || field.type === 'segmented') return opt(value);
  return String(value);
}

/**
 * Сводка ответов по шагам: [{ stepId, stepTitle, items: [{ id, label, value }] }].
 * Пустые необязательные поля пропускаются.
 */
export function summarize(schema, state) {
  const clean = prune(schema, state);
  return visibleSteps(schema, clean).map((s) => ({
    stepId: s.id,
    stepTitle: s.title,
    items: visibleFields(s, clean)
      .filter((f) => !isEmpty(clean[f.id]))
      .map((f) => ({ id: f.id, label: f.label, value: displayValue(f, clean[f.id]) })),
  }));
}

/** Сводка одной строкой на поле — для заявки и копирования в буфер. */
export const summaryText = (summary) =>
  summary.flatMap((g) => g.items.map((i) => `${i.label}: ${i.value}`)).join('\n');

/**
 * Ответы из адресной строки (?buildingType=house&technology=frame).
 * Принимаются только известные поля и допустимые варианты.
 */
export function stateFromQuery(schema, search) {
  const q = new URLSearchParams(search);
  const st = {};
  for (const s of schema.steps) {
    for (const f of s.fields) {
      if (!q.has(f.id)) continue;
      const raw = q.get(f.id);
      if (f.type === 'multi') {
        const vals = raw.split(',').filter((v) => f.options.some((o) => o.value === v));
        if (vals.length) st[f.id] = vals;
      } else if (f.options) {
        if (f.options.some((o) => o.value === raw)) st[f.id] = raw;
      } else if (f.type === 'number') {
        if (!Number.isNaN(parseNumber(raw))) st[f.id] = raw;
      }
    }
  }
  return st;
}
