import {AxeBuilder} from '@axe-core/playwright';
import {expect, test} from '@playwright/test';

/** axe on every page: no serious or critical issues (WCAG 2.2 AA; 09-build-plan.md, phase 6). */
const PAGES = ['/', '/dev/tokens', '/nothing-here'];

for (const path of PAGES) {
  test(`axe: ${path}`, async ({page}) => {
    await page.goto(path);
    const results = await new AxeBuilder({page}).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
    const serious = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
    for (const v of results.violations) console.log(`[axe] ${path} ${v.impact}: ${v.id} (${v.nodes.length}) ${v.help}`);
    expect(serious.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)).toEqual([]);
  });
}
