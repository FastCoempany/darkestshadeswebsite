import {expect, test} from '@playwright/test';

const STORYBOOK = process.env.STORYBOOK_URL ?? 'http://localhost:6006';

/** The pop-up listens for scroll after hydration: scroll past 60%, then nudge once (as behaviour.spec does). */
async function scrollToOffer(page: import('@playwright/test').Page) {
  await page.evaluate(() => window.scrollTo(0, (document.documentElement.scrollHeight - window.innerHeight) * 0.7));
  await page.waitForTimeout(100);
  await page.evaluate(() => window.scrollBy(0, 10));
}

/**
 * The keyboard pass (09-build-plan.md, phase 6): the entry, the menu, the bag, the gallery, the pop-up and
 * the sign-up, by keys alone. Focus is visible everywhere (base.css); nothing needs a pointer.
 */
test.describe('keyboard', () => {
  test.describe('the opening', () => {
    test('Skip intro is focused first, Tab wraps inside the notice, Enter skips to the page', async ({page}) => {
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

    test('Esc on the notice skips too', async ({page}) => {
      await page.goto('/');
      await expect(page.locator('[data-sensory-notice]')).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(page.locator('[data-sensory-notice]')).toHaveCount(0);
      await expect(page.locator('[data-manifesto]')).toBeVisible();
      expect((await page.context().cookies()).find((c) => c.name === 'ds_entry')?.value).toBe('seen');
    });

    test('Continue by Enter starts the sequence with Skip focused; Tab stays on Skip; Enter skips from the first frame', async ({page}) => {
      await page.goto('/');
      await page.keyboard.press('Tab');
      await expect(page.getByRole('button', {name: 'Continue'})).toBeFocused();
      await page.keyboard.press('Enter');
      const entry = page.locator('[data-entry]');
      await expect(entry).toHaveAttribute('data-entry', 'card');
      const skip = page.getByRole('button', {name: 'Skip'});
      await expect(skip).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(skip).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(entry).toHaveCount(0);
      await expect(page.locator('[data-manifesto]')).toBeVisible();
      expect((await page.context().cookies()).find((c) => c.name === 'ds_entry')?.value).toBe('seen');
    });
  });

  test.describe('with the opening seen', () => {
    test.beforeEach(async ({context}) => {
      await context.addCookies([{name: 'ds_entry', value: 'seen', url: 'http://localhost:3000'}]);
    });

    test('the skip link is first, then the header; the menu opens, wraps both ways and closes by keys', async ({page}, testInfo) => {
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
      const close = menu.getByRole('button', {name: 'Close'});
      const last = menu.getByRole('link', {name: /@darkestshades/});
      await expect(close).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(menu.getByRole('link', {name: 'Drop', exact: true})).toBeFocused();
      // Backwards past the first stop lands on the last; forwards past the last lands on the first.
      await page.keyboard.press('Shift+Tab');
      await page.keyboard.press('Shift+Tab');
      await expect(last).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(close).toBeFocused();
      await page.keyboard.press('Escape');
      await expect(menu).toHaveCount(0);
      await expect(page.getByRole('button', {name: 'Menu'})).toBeFocused();
    });

    test('the header is reachable by Tab on desktop: skip link, mark, the three links, the bag', async ({page}, testInfo) => {
      test.skip(testInfo.project.name !== 'app-1440', 'the inline nav is the desktop header');
      await page.goto('/frames');
      await page.keyboard.press('Tab');
      await expect(page.getByRole('link', {name: 'Skip to content'})).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(page.getByRole('link', {name: 'Darkest Shades'}).first()).toBeFocused();
      for (const name of ['Drop', 'Frames', 'Manifesto']) {
        await page.keyboard.press('Tab');
        await expect(page.getByRole('navigation', {name: 'Primary'}).getByRole('link', {name, exact: true})).toBeFocused();
      }
      await page.keyboard.press('Tab');
      await expect(page.getByRole('button', {name: /^Bag/})).toBeFocused();
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

    test('a bag line changes its quantity and is removed by keys', async ({page}) => {
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
      const lines = bag.getByRole('listitem');
      const before = await lines.count();
      await bag.getByRole('button', {name: 'Remove'}).first().focus();
      await page.keyboard.press('Enter');
      await expect(lines).toHaveCount(before - 1);
    });

    test('the gallery moves with the arrow keys on a phone', async ({page}, testInfo) => {
      test.skip(testInfo.project.name !== 'app-390', 'the swipe track is the phone gallery');
      await page.goto('/frames/lou-went-underground');
      const track = page.getByRole('list', {name: 'Pictures of Lou Went Underground'});
      await track.focus();
      await page.keyboard.press('ArrowRight');
      await expect(page.getByText(/^2 \/ \d+$/)).toBeVisible();
      await page.keyboard.press('ArrowLeft');
      await expect(page.getByText(/^1 \/ \d+$/)).toBeVisible();
    });

    test('a picture zooms in and out with Enter on its control', async ({page}) => {
      await page.goto('/frames/lou-went-underground');
      const zoomIn = page.getByRole('button', {name: /^Zoom in/}).first();
      await zoomIn.focus();
      await page.keyboard.press('Enter');
      await expect(page.locator('[data-gallery]')).toHaveAttribute('data-gallery-state', 'zoomed');
      const zoomOut = page.getByRole('button', {name: /^Zoom out/}).first();
      await expect(zoomOut).toBeVisible();
      await zoomOut.focus();
      await page.keyboard.press('Enter');
      await expect(page.locator('[data-gallery]')).not.toHaveAttribute('data-gallery-state', 'zoomed');
    });

    test('the list pop-up keeps focus inside, closes on Not now by Tab and Enter, and leaves focus on the page', async ({page}) => {
      await page.goto('/frames/lou-went-underground');
      await scrollToOffer(page);
      const dialog = page.getByRole('dialog', {name: 'The list hears first.'});
      await expect(dialog).toBeVisible();
      await expect(dialog.locator(':focus')).toHaveCount(1);
      for (let i = 0; i < 12; i++) {
        await page.keyboard.press('Tab');
        await expect(dialog.locator(':focus')).toHaveCount(1);
      }
      const notNow = dialog.getByRole('button', {name: 'Not now'});
      for (let i = 0; i < 12 && !(await notNow.evaluate((el) => el === document.activeElement)); i++) await page.keyboard.press('Tab');
      await expect(notNow).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(dialog).toHaveCount(0);
      await expect(page.locator('body')).toBeFocused();
      expect((await page.context().cookies()).find((c) => c.name === 'ds_offer')?.value).toBe('closed');
    });

    test('the list pop-up closes on Esc', async ({page}) => {
      await page.goto('/frames/lou-went-underground');
      await scrollToOffer(page);
      const dialog = page.getByRole('dialog', {name: 'The list hears first.'});
      await expect(dialog).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(dialog).toHaveCount(0);
      await expect(page.locator('body')).toBeFocused();
    });

    test('the sign-up form is filled, consented and sent by keys', async ({page}) => {
      await page.goto('/frames');
      const form = page.locator('[data-list-form="footer"]');
      await form.getByLabel('Email').focus();
      await page.keyboard.type('keys@example.com');
      await page.keyboard.press('Tab');
      await expect(form.getByLabel('Country')).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(form.getByLabel('Mobile number (optional)')).toBeFocused();
      await page.keyboard.type('4155550123');
      await page.keyboard.press('Tab');
      const consent = form.getByRole('checkbox');
      await expect(consent).toBeFocused();
      await page.keyboard.press('Space');
      await expect(consent).toBeChecked();
      await page.keyboard.press('Tab');
      await expect(form.getByRole('link', {name: 'Privacy'})).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(form.getByRole('link', {name: 'SMS terms'})).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(form.getByRole('button', {name: 'Join the list'})).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(page.getByText("You're on the list.")).toBeVisible();
    });
  });
});
