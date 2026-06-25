import { test } from '@playwright/test';

const pages = [
  ['landing', '/'],
  ['login', '/login'],
  ['register', '/register'],
  ['chat', '/app'],
  ['admin', '/app/admin'],
  ['load-tests', '/app/load-tests'],
  ['observability', '/app/observability'],
  ['mlops', '/app/mlops']
];

test.describe('documentation screenshots', () => {
  for (const [name, path] of pages) {
    test(`screenshot ${name}`, async ({ page }) => {
      await page.goto(`http://localhost:3000${path}`);
      await page.screenshot({ path: `../docs/screenshots/${name}.png`, fullPage: true });
    });
  }
});
