import {expect, test} from '@playwright/test';

const STORYBOOK = process.env.STORYBOOK_URL ?? 'http://localhost:6006';

/**
 * The keyboard pass (09-build-plan.md, phase 6): the entry, the menu, the bag, the gallery, the pop-up and
 * the sign-up, by keys alone. Focus is visible everywhere (base.css); nothing needs a pointer.
 */
test.describe('keyboard', () => {
  test('the opening: Skip intro is focused first, Tab wraps inside the notice, Enter skips to the page', async ({page}) => {
    await page.goto('/');
    const notice = page.locator('[data-sensory-notice]');
    await expect(notice).toBeVisible();
    await expect(page.getByRole('button', {name: 'Skip intro'})).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', {name: 'Continue'})).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', {name: 'Skip intro'})).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(notice).toHaveCount(0);
    await expect(page.locator('[data-manifesto]')).toBeVisible();
    expect((await page.context().cookies()).find((c) => c.name === 'ds_entry')?.value).toBe('seen');
  });

  test.describe('with the opening seen', () => {
    test.beforeEach(async ({context}) => {
      await context.addCookies([{name: 'ds_entry', value: 'seen', url: 'http://localhost:3000'}]);
    });

    test('the skip link is first, then the header; the menu opens, wraps and closes by keys', async ({page}, testInfo) => {
      test.skip(testInfo.project.name !== 'app-390', 'the menu sheet is the phone header');
      await page.goto('/frames');
      await page.keyboard.press('Tab');
      await expect(page.getByRole('link', {name: 'Skip to content'})).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(page.getByRole('link', {name: 'Darkest Shades'}).first()).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(page.getByRole('button', {name: 'Menu'})).toBeFocused();
      await page.keyboard.press('Enter');
      const menu = page.getByRole('dialog', {name: 'Menu'});
      await expect(menu).toBeVisible();
      await expect(menu.getByRole('button', {name: 'Close'})).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(menu.getByRole('link', {name: 'Drop', exact: true})).toBeFocused();
      await page.keyboard.press('Shift+Tab');
      await page.keyboard.press('Shift+Tab');
      await expect(menu.locator(':focus')).toHaveCount(1);
      await page.keyboard.press('Escape');
      await expect(menu).toHaveCount(0);
      await expect(page.getByRole('button', {name: 'Menu'})).toBeFocused();
    });

    test('the bag opens from the header, keeps focus inside, closes with Esc and gives focus back', async ({page}) => {
      await page.goto('/frames');
      const bagButton = page.getByRole('button', {name: /^Bag/});
      await bagButton.focus();
      await page.keyboard.press('Enter');
      const bag = page.getByRole('dialog', {name: 'Bag'});
      await expect(bag).toBeVisible();
      await expect(bag.locator(':focus')).toHaveCount(1);
      for (let i = 0; i < 6; i++) {
        await page.keyboard.press('Tab');
        await expect(bag.locator(':focus')).toHaveCount(1);
      }
      await page.keyboard.press('Escape');
      await expect(bag).toHaveCount(0);
      await expect(bagButton).toBeFocused();
    });

    test('a bag line changes its quantity by keys', async ({page}) => {
      await page.goto(`${STORYBOOK}/iframe.html?id=pages-overlays--bag-drawer-open&viewMode=story`);
      const bag = page.getByRole('dialog', {name: 'Bag'});
      await expect(bag).toBeVisible();
      const line = bag.getByRole('group', {name: 'Quantity'}).first();
      const more = line.getByRole('button', {name: 'More'});
      await more.focus();
      await page.keyboard.press('Enter');
      await expect(line.locator('output')).toHaveText('2');
      // Fewer was disabled at 1; it is the previous stop now.
      await page.keyboard.press('Shift+Tab');
      await expect(line.getByRole('button', {name: 'Fewer'})).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(line.locator('output')).toHaveText('1');
    });

    test('the gallery moves with the arrow keys and zooms with Enter on a phone', async ({page}, testInfo) => {
      test.skip(testInfo.project.name !== 'app-390', 'the swipe track is the phone gallery');
      await page.goto('/frames/lou-went-underground');
      const track = page.getByRole('list', {name: 'Pictures of Lou Went Underground'});
      await track.focus();
      await page.keyboard.press('ArrowRight');
      await expect(page.getByText('2 / 8')).toBeVisible();
      await page.keyboard.press('ArrowLeft');
      await expect(page.getByText('1 / 8')).toBeVisible();
      await page.keyboard.press('Tab');
      const zoom = page.getByRole('button', {name: /^Zoom in/}).first();
      await expect(zoom).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(page.getByRole('button', {name: /^Zoom out/}).first()).toBeVisible();
      await expect(page.locator('[data-gallery]')).toHaveAttribute('data-gallery-state', 'zoomed');
    });

    test('the list pop-up keeps focus inside and closes on Not now', async ({page}) => {
      await page.goto('/frames/lou-went-underground');
      await page.evaluate(() => window.scrollTo(0, (document.documentElement.scrollHeight - window.innerHeight) * 0.7));
      const dialog = page.getByRole('dialog', {name: 'The list hears first.'});
      await expect(dialog).toBeVisible({timeout: 10_000});
      for (let i = 0; i < 12; i++) {
        await page.keyboard.press('Tab');
        await expect(dialog.locator(':focus')).toHaveCount(1);
      }
      await dialog.getByRole('button', {name: 'Not now'}).focus();
      await page.keyboard.press('Enter');
      await expect(dialog).toHaveCount(0);
      expect((await page.context().cookies()).find((c) => c.name === 'ds_offer')?.value).toBe('closed');
    });

    test('the sign-up form works by keys alone', async ({page}) => {
      await page.goto('/frames');
      const form = page.locator('[data-list-form="footer"]');
      await form.getByLabel('Email').focus();
      await page.keyboard.type('keys@example.com');
      for (let i = 0; i < 6; i++) await page.keyboard.press('Tab');
      await expect(form.getByRole('button', {name: 'Join the list'})).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(page.getByText("You're on the list.")).toBeVisible();
    });
  });
});
