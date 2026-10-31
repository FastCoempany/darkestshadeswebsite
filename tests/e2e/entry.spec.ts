import {expect, test} from '@playwright/test';

/**
 * The opening (03-references.md): the photosensitivity notice first, then the sequence from still
 * images on a frame clock, skippable from the first frame, remembered for 30 days, never on deep links.
 */
test.describe('the opening', () => {
  test('first visit: the notice, then the sequence, then the home page; the visit is remembered', async ({page}) => {
    test.setTimeout(120_000);
    await page.goto('/');
    const notice = page.locator('[data-sensory-notice]');
    await expect(notice).toBeVisible();
    await expect(page.getByRole('button', {name: 'Skip intro'})).toBeFocused();
    await page.getByRole('button', {name: 'Continue'}).click();
    const entry = page.locator('[data-entry]');
    await expect(entry).toHaveAttribute('data-entry', 'card');
    await expect(page.getByRole('button', {name: 'Skip'})).toBeFocused();
    await expect(entry).toHaveAttribute('data-entry', 'burst', {timeout: 5000});
    // A burst frame carries a graded still from assets/entry.
    await expect(page.locator('[data-burst] img').first()).toHaveAttribute('src', /\/entry\/b1-/);
    await expect(entry).toHaveAttribute('data-entry', 'logo', {timeout: 10_000});
    await expect(entry).toHaveAttribute('data-entry', 'end', {timeout: 10_000});
    await expect(entry).toHaveCount(0, {timeout: 5000});
    await expect(page.locator('[data-manifesto]')).toBeVisible();
    const cookies = await page.context().cookies();
    expect(cookies.find((c) => c.name === 'ds_entry')?.value).toBe('seen');
  });

  test('Esc skips from the first frame and sets the cookie', async ({page}) => {
    await page.goto('/');
    await page.getByRole('button', {name: 'Continue'}).click();
    await expect(page.locator('[data-entry]')).toHaveAttribute('data-entry', 'card');
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-entry]')).toHaveCount(0);
    expect((await page.context().cookies()).find((c) => c.name === 'ds_entry')?.value).toBe('seen');
  });

  test('Skip intro on the notice goes straight to the page', async ({page}) => {
    await page.goto('/');
    await page.getByRole('button', {name: 'Skip intro'}).click();
    await expect(page.locator('[data-sensory-notice]')).toHaveCount(0);
    await expect(page.locator('[data-entry]')).toHaveCount(0);
  });

  test('never on a deep link, a campaign parameter or a returning visit', async ({page, context}) => {
    await page.goto('/?utm_source=instagram');
    await expect(page.locator('[data-sensory-notice]')).toHaveCount(0);
    await page.goto('/frames');
    await expect(page.locator('[data-sensory-notice]')).toHaveCount(0);
    await context.addCookies([{name: 'ds_entry', value: 'seen', url: 'http://localhost:3000'}]);
    await page.goto('/');
    await expect(page.locator('[data-sensory-notice]')).toHaveCount(0);
    await expect(page.locator('[data-manifesto]')).toBeVisible();
  });

  test('reduced motion: the cards only, no bursts', async ({browser}) => {
    const context = await browser.newContext({
      reducedMotion: 'reduce',
      viewport: {width: 390, height: 844},
      baseURL: 'http://localhost:3000',
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
    });
    const page = await context.newPage();
    await page.goto('/');
    await page.getByRole('button', {name: 'Continue'}).click();
    const seen = new Set<string>();
    for (let i = 0; i < 40; i++) {
      const entry = page.locator('[data-entry]');
      if ((await entry.count()) === 0) break;
      const kind = await entry.first().getAttribute('data-entry');
      if (kind) seen.add(kind);
      await page.waitForTimeout(250);
    }
    expect(seen.has('burst')).toBe(false);
    expect(seen.has('card')).toBe(true);
    await context.close();
  });

  test('the Accessibility page turns the opening off for a year', async ({page}) => {
    await page.goto('/accessibility');
    await page.getByRole('button', {name: 'Off'}).click();
    await expect(page.getByText('Saved.')).toBeVisible();
    expect((await page.context().cookies()).find((c) => c.name === 'ds_entry')?.value).toBe('off');
    await page.goto('/');
    await expect(page.locator('[data-sensory-notice]')).toHaveCount(0);
  });
});
