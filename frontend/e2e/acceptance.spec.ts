import { expect, test, type Page } from '@playwright/test';
import { appendixA5PlanCheck, appendixALookup } from './helpers';

const VIEWPORT_H = 768;

async function bottomOf(page: Page, selector: string) {
  const box = await page.locator(selector).first().boundingBox();
  if (!box) throw new Error(`${selector} not rendered`);
  return box.y + box.height;
}

test('Appendix A: all figures, the Rule 56(1)(a) citation and the amendment notice are above the fold', async ({ page }) => {
  await page.goto('/');
  await appendixALookup(page); // 3 entries + 1 click = 4 (NFR-09)

  const cards = page.locator('main article[aria-labelledby^="fig-"]');
  await expect(cards).toHaveCount(8);
  for (const box of await cards.evaluateAll((els) => els.map((e) => e.getBoundingClientRect().bottom))) {
    expect(box).toBeLessThanOrEqual(VIEWPORT_H);
  }
  expect(await bottomOf(page, 'main a[href="#amendments"]')).toBeLessThanOrEqual(VIEWPORT_H);
  expect(await bottomOf(page, 'main h3:has-text("Rule 56(1)(a): Residential Buildings")')).toBeLessThanOrEqual(VIEWPORT_H);

  const scrollW = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(scrollW).toBeLessThanOrEqual(1366); // no horizontal scroll
});

test('A.5 plan check draws the envelope, footprint and labelled 0.60 m front strip', async ({ page }) => {
  await page.goto('/');
  await appendixA5PlanCheck(page); // 11 entries + 1 click = 12 (NFR-10)
  const svg = page.getByRole('img', { name: /Plot 10.00 m by 20.00 m/ });
  await expect(svg.getByText('7.50 x 14.50 m')).toBeVisible();
  await expect(svg.getByText('108.75 sq m')).toBeVisible();
  await expect(svg.getByText('113.25 sq m')).toBeVisible();
  await expect(svg.getByText('0.60 m short, R56(1)(a), p. 77')).toBeVisible();
  await expect(svg.locator('rect[fill^="url(#hatch"]')).toHaveCount(1);
});

test('height 10.5 shows the side-space notice', async ({ page }) => {
  await page.goto('/');
  await appendixA5PlanCheck(page);
  await page.getByLabel('Proposed building height').fill('10.5');
  await expect(page.getByText('Left open space changed from 2.50 m to 3.00 m because the height changed.')).toBeVisible();
});

test('print: the slip fits one A4 page and contains every required element', async ({ page }) => {
  await page.goto('/');
  await appendixA5PlanCheck(page);
  await page.emulateMedia({ media: 'print' });
  const slip = page.locator('.print-slip');
  await expect(slip).toBeVisible();
  for (const text of [
    'Counter slip',
    'Derived from MP Bhumi Vikas Rules 2012',
    'Setback conflict found',
    'Potentially relevant amendment',
    'The building-permission clerk decides',
    'Official PDF page 77',
  ]) {
    // Skip the drawing's <title>, which repeats the result text but is never rendered.
    await expect(slip.locator('*:not(title)', { hasText: text }).last()).toBeVisible();
  }
  await expect(page.locator('aside[aria-label]')).toBeHidden(); // intake hidden

  const pdf = await page.pdf({ format: 'A4', printBackground: true, preferCSSPageSize: true });
  const pages = (pdf.toString('latin1').match(/\/Type\s*\/Page[^s]/g) ?? []).length;
  expect(pages).toBe(1);
});

test('Hindi: labels in Devanagari with Noto Sans Devanagari, rule text unchanged in English', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'हिन्दी' }).click();
  await page.getByLabel('प्लॉट का क्षेत्रफल').fill('200');
  await page.getByLabel('सड़क की चौड़ाई').fill('9');
  await page.getByLabel('आवेदन शुल्क').uncheck();
  await page.getByLabel('अनुज्ञा शुल्क').uncheck();
  await page.getByRole('button', { name: 'खोजें' }).click();

  const label = page.getByRole('heading', { name: 'सामने की न्यूनतम खुली जगह' });
  await expect(label).toBeVisible();
  const loaded = await page.evaluate(async () => {
    await document.fonts.ready;
    return document.fonts.check('16px "Noto Sans Devanagari"', 'सामने');
  });
  expect(loaded).toBe(true);
  expect(await label.evaluate((el) => getComputedStyle(el).fontFamily)).toContain('Noto Sans Devanagari');
  await expect(page.getByRole('region', { name: '56(1)(a)' })).toContainText('Up to 9.0 meters');
});

test('keyboard only: reach the form, fill it, submit with Enter; focus is visible', async ({ page }) => {
  await page.goto('/');
  for (let i = 0; i < 25; i++) {
    await page.keyboard.press('Tab');
    if ((await page.evaluate(() => document.activeElement?.id)) === 'field-plot_area') break;
  }
  expect(await page.evaluate(() => document.activeElement?.id)).toBe('field-plot_area');
  const outline = await page.evaluate(() => getComputedStyle(document.activeElement as Element).outlineStyle);
  expect(outline).not.toBe('none');

  await page.keyboard.type('200');
  await page.keyboard.press('Tab');
  await page.keyboard.type('9');
  await page.keyboard.press('Tab'); // use type (residential by default)
  await page.keyboard.press('Tab');
  await page.keyboard.type('250');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: /Rule 56\(1\)\(a\)/ })).toBeVisible();
});

test('no request leaves the local server', async ({ page }) => {
  const external: string[] = [];
  page.on('request', (req) => {
    const url = new URL(req.url());
    if (!['127.0.0.1:5173', 'localhost:5173'].includes(url.host) && url.protocol !== 'data:') external.push(req.url());
  });
  await page.goto('/');
  await appendixALookup(page);
  await page.goto('/');
  await appendixA5PlanCheck(page);
  expect(external).toEqual([]);
});

test('not found, blocked and refused states render', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Type the question (English or Hindi)').fill('What is the current market rate for land in Kolar Road, Bhopal?');
  await page.getByRole('button', { name: 'Fill form from text' }).click();
  await expect(page.getByText(/No plot details found/)).toBeVisible();
  await page.getByRole('button', { name: 'Look up', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Not found in MP Bhumi Vikas Rules 2012' })).toBeVisible();

  await page.goto('/');
  await appendixA5PlanCheck(page);
  await page.getByLabel('Plot area').fill('230');
  await page.getByRole('button', { name: 'Run plan check' }).click();
  await expect(page.getByRole('heading', { name: /Plan check stopped/ })).toBeVisible();

  await page.goto('/');
  await page.getByLabel('Two or more streets (corner plot)').check();
  await page.getByLabel('Plot area').fill('200');
  await page.getByLabel('Road width').fill('9');
  await page.getByLabel('Proposed built-up area').fill('250');
  await page.getByLabel('Proposed building height').fill('10');
  await page.getByLabel('Development type').selectOption('semi_detached');
  await page.getByLabel('Plot frontage (width along road)').fill('10');
  await page.getByLabel('Plot depth').fill('20');
  for (const [label, v] of [['From front boundary', '2.4'], ['From rear boundary', '2.5'], ['From left boundary', '2.5'], ['From right boundary', '0']] as const) {
    await page.getByLabel(label).fill(v);
  }
  await page.getByRole('button', { name: 'Run plan check' }).click();
  await expect(page.getByRole('heading', { name: 'Plan check not available for this case' })).toBeVisible();
});
