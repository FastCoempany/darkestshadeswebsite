import {expect, test} from '@playwright/test';
import {settle} from './helpers';

/** Phase 0's screenshot test: the token sheet at 390 and 1440 (the project viewports), in UI and wire mode. */
test.describe('token sheet', () => {
  for (const mode of ['ui', 'wire'] as const) {
    test(`renders in ${mode} mode`, async ({page}) => {
      await page.goto(mode === 'wire' ? '/dev/tokens?mode=wire' : '/dev/tokens');
      await expect(page.getByRole('heading', {level: 1})).toHaveText('Darkest Shades foundation');
      await settle(page);
      await expect(page.locator('html')).toHaveAttribute('data-theme', 'night');
      if (mode === 'wire') await expect(page.locator('html')).toHaveAttribute('data-mode', 'wire');
      await expect(page).toHaveScreenshot(`tokens-${mode}.png`, {fullPage: true});
    });
  }
});
