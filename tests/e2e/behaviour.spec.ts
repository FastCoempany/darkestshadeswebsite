import {expect, test} from '@playwright/test';

/** The house layer's behaviours (05): the detail hold's push, the header's surface, the pop-up, the bag, the menu. */
test.describe('house behaviours', () => {
  test.beforeEach(async ({context}) => {
    await context.addCookies([{name: 'ds_entry', value: 'seen', url: 'http://localhost:3000'}]);
  });

  test('the detail hold pushes in with the scroll and nothing else moves', async ({page}) => {
    await page.goto('/');
    const hold = page.locator('[data-detail-hold]');
    await hold.scrollIntoViewIfNeeded();
    await page.waitForTimeout(100);
    const progress = await hold.evaluate((el) => parseFloat(getComputedStyle(el).getPropertyValue('--detail-progress')));
    expect(progress).toBeGreaterThan(0);
    expect(progress).toBeLessThanOrEqual(1);
    const scale = await hold.locator('img').first().evaluate((img) => getComputedStyle(img).transform);
    expect(scale).toMatch(/matrix\(1\.0\d+|matrix\(1,/);
  });

  test('the header is transparent over the manifesto and solid once it has passed', async ({page}) => {
    await page.goto('/');
    await expect(page.locator('header')).toHaveAttribute('data-surface', 'transparent');
    await page.evaluate(() => window.scrollTo(0, window.innerHeight * 2));
    await expect(page.locator('header')).toHaveAttribute('data-surface', 'transparent');
    // Just past the manifesto's bottom edge.
    await page.evaluate(() => {
      const m = document.querySelector('[data-manifesto]')!.getBoundingClientRect();
      window.scrollTo(0, window.scrollY + m.bottom + 24);
    });
    await expect(page.locator('header')).toHaveAttribute('data-surface', 'solid');
  });

  test('the list pop-up opens once at 60% scroll on a frame page and stays away after closing', async ({page}) => {
    await page.goto('/frames/lou-went-underground');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await page.evaluate(() => window.scrollTo(0, (document.documentElement.scrollHeight - window.innerHeight) * 0.7));
    await page.waitForTimeout(100);
    await page.evaluate(() => window.scrollBy(0, 10));
    const dialog = page.getByRole('dialog', {name: 'The list hears first.'});
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(/discount|% off/i)).toHaveCount(0);
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    expect((await page.context().cookies()).find((c) => c.name === 'ds_offer')?.value).toBe('closed');
    await page.reload();
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await page.waitForTimeout(300);
    await expect(page.getByRole('dialog')).toHaveCount(0);
  });

  test('the list pop-up opens on the home page, never on a policy page', async ({page}) => {
    await page.goto('/policies/privacy');
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await page.waitForTimeout(200);
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await page.goto('/');
    await page.evaluate(() => window.scrollTo(0, (document.documentElement.scrollHeight - window.innerHeight) * 0.7));
    await page.waitForTimeout(100);
    await page.evaluate(() => window.scrollBy(0, 10));
    await expect(page.getByRole('dialog', {name: 'The list hears first.'})).toBeVisible();
  });

  test('the bag drawer opens from the header, traps focus, and closes with Esc back to the opener', async ({page}) => {
    await page.goto('/frames');
    const opener = page.getByRole('button', {name: 'Bag'});
    await opener.click();
    const dialog = page.getByRole('dialog', {name: 'Bag'});
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('button', {name: 'Close'})).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(dialog.locator(':focus')).toHaveCount(1);
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    await expect(opener).toBeFocused();
  });

  test('the list form validates, needs consent for texts, and records a sign-up in the mock', async ({page}) => {
    await page.goto('/frames');
    const form = page.locator('[data-list-form="footer"]');
    await form.getByRole('button', {name: 'Join the list'}).click();
    await expect(form.getByText('Enter an email address like name@example.com.')).toBeVisible();
    await form.getByLabel('Email').fill('name@example.com');
    await form.getByLabel('Mobile number (optional)').fill('415 555 0123');
    await form.getByRole('button', {name: 'Join the list'}).click();
    await expect(form.getByText('Check the box to get texts, or leave the number empty.')).toBeVisible();
    await form.getByRole('checkbox').check();
    await form.getByRole('button', {name: 'Join the list'}).click();
    await expect(page.getByText("You're on the list.")).toBeVisible();
    const stored = await page.evaluate(() => window.localStorage.getItem('ds_list'));
    expect(stored).toContain('name@example.com');
  });
});

/** A missing path, frame, drop or policy is a 404 titled as one: only the root's meta runs when a loader throws. */
test.describe('404 titles', () => {
  for (const path of ['/nothing-here', '/frames/nothing-here', '/drops/999', '/policies/nothing']) {
    test(`${path} is titled as the 404`, async ({page}) => {
      const response = await page.goto(path);
      expect(response?.status()).toBe(404);
      await expect(page).toHaveTitle(/This page doesn't exist\. · Darkest Shades/);
      await expect(page.locator('[data-page="not-found"][data-status="404"]')).toHaveCount(1);
    });
  }
});
