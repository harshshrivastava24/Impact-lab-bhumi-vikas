import type { Page } from '@playwright/test';

/** Appendix A lookup from a blank form: 3 entries plus the Look up click. */
export async function appendixALookup(page: Page) {
  await page.getByLabel('Plot area').fill('200');
  await page.getByLabel('Road width').fill('9');
  await page.getByLabel('Proposed built-up area').fill('250');
  await page.getByRole('button', { name: 'Look up', exact: true }).click();
  await page.getByRole('heading', { name: /Rule 56\(1\)\(a\)/ }).waitFor();
}

/** Appendix A.5 plan check from a blank form: 11 entries plus the Run plan check click. */
export async function appendixA5PlanCheck(page: Page, height = '10') {
  await page.getByLabel('Plot area').fill('200');
  await page.getByLabel('Road width').fill('9');
  await page.getByLabel('Proposed built-up area').fill('250');
  await page.getByLabel('Proposed building height').fill(height);
  await page.getByLabel('Development type').selectOption('semi_detached');
  await page.getByLabel('Plot frontage (width along road)').fill('10');
  await page.getByLabel('Plot depth').fill('20');
  await page.getByLabel('From front boundary').fill('2.4');
  await page.getByLabel('From rear boundary').fill('2.5');
  await page.getByLabel('From left boundary').fill('2.5');
  await page.getByLabel('From right boundary').fill('0');
  await page.getByRole('button', { name: 'Run plan check' }).click();
  await page.getByRole('img', { name: /Plot 10.00 m by 20.00 m/ }).waitFor();
}
