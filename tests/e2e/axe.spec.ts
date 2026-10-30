import {AxeBuilder} from '@axe-core/playwright';
import {expect, test} from '@playwright/test';

/** axe on every page: no serious or critical issues (WCAG 2.2 AA; 09-build-plan.md, phase 6). */
const PAGES = ['/', '/drops/001', '/frames', '/frames/lou-went-underground', '/frames/what-arnie-hid', '/manifesto', '/cast', '/questions', '/care', '/policies', '/policies/exchange', '/accessibility', '/cart', '/account', '/dev/tokens', '/nothing-here'];

for (const path of PAGES) {
  test(`axe: ${path}`, async ({page, context}) => {
    await context.addCookies([{name: 'ds_entry', value: 'seen', url: 'http://localhost:3000'}]);
    await page.goto(path);
    const results = await new AxeBuilder({page}).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
    const serious = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
    for (const v of results.violations) console.log(`[axe] ${path} ${v.impact}: ${v.id} (${v.nodes.length}) ${v.help}`);
    expect(serious.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)).toEqual([]);
  });
}
