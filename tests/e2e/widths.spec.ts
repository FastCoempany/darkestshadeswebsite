import {expect, test} from '@playwright/test';
import {settle} from './helpers';

/**
 * Every page works at 320 px wide and at 200% zoom (04, Breakpoints): no horizontal overflow at 320,
 * 768 and 1024 (a 1440 screen at 200% zoom lays out like 720), and the main landmark is present.
 */
const PAGES = ['/', '/drops/001', '/frames', '/frames/lou-went-underground', '/manifesto', '/cast', '/questions', '/accessibility', '/cart'];
const WIDTHS = [320, 720, 768, 1024];

test.describe('widths', () => {
  for (const width of WIDTHS) {
    for (const path of PAGES) {
      test(`${path} fits ${width}px`, async ({browser}) => {
        const context = await browser.newContext({viewport: {width, height: 900}, deviceScaleFactor: 1});
        await context.addCookies([{name: 'ds_entry', value: 'seen', url: 'http://localhost:3000'}]);
        const page = await context.newPage();
        await page.goto(`http://localhost:3000${path}`);
        await settle(page);
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        expect(overflow, `${path} overflows by ${overflow}px at ${width}`).toBeLessThanOrEqual(0);
        await expect(page.locator('main#main')).toHaveCount(1);
        await context.close();
      });
    }
  }
});
