// Запуск тестов в Node.js 18+:  node tests/run.mjs
import { readFile } from 'node:fs/promises';
import { engineTests, pricingTests } from './suite.js';

const load = async (p) => JSON.parse(await readFile(new URL(p, import.meta.url), 'utf8'));
const schema = await load('../content/calculator.json');
const cases = await load('./pricing-cases.json');

let fail = 0;
for (const [title, res] of [['Логика анкеты', engineTests(schema)], ['Контрольные примеры', pricingTests(schema, cases)]]) {
  console.log(`\n${title}`);
  for (const r of res) {
    console.log(`  ${r.ok ? '✓' : '✗'} ${r.name}${r.ok ? '' : `\n      ${r.detail}`}`);
    if (!r.ok) fail += 1;
  }
}
console.log(fail ? `\nПровалено: ${fail}` : '\nВсе проверки пройдены');
process.exit(fail ? 1 : 0);
