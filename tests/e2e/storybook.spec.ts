import {readFileSync} from 'node:fs';
import {AxeBuilder} from '@axe-core/playwright';
import {expect, test} from '@playwright/test';
import {settle} from './helpers';

/**
 * The component matrix (05-components.md): every story at 390 and 1440, in UI and wire mode, with a
 * screenshot each and axe in UI mode. Reads storybook-static/index.json, so a new story joins the
 * matrix on its own.
 */
type Entry = {id: string; title: string; name: string; type: string; tags?: string[]};
const index = JSON.parse(readFileSync('storybook-static/index.json', 'utf8')) as {entries: Record<string, Entry>};
const stories = Object.values(index.entries).filter((e) => e.type === 'story' && !e.tags?.includes('skip-matrix'));

const SIZES = [
  {name: '390', width: 390, height: 844},
  {name: '1440', width: 1440, height: 900},
];

for (const story of stories) {
  for (const size of SIZES) {
    for (const mode of ['ui', 'wire'] as const) {
      test(`${story.title} / ${story.name} @ ${size.name} ${mode}`, async ({page}) => {
        await page.setViewportSize({width: size.width, height: size.height});
        await page.goto(`/iframe.html?id=${story.id}&viewMode=story&globals=mode:${mode}`);
        await page.waitForSelector('#storybook-root > *', {state: 'attached'});
        await settle(page);
        await page.waitForTimeout(150);
        if (mode === 'wire') await expect(page.locator('html')).toHaveAttribute('data-mode', 'wire');
        await expect(page).toHaveScreenshot(`${story.id}--${size.name}-${mode}.png`, {fullPage: true});
        if (mode === 'ui') {
          const results = await new AxeBuilder({page}).include('#storybook-root').withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
          const serious = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
          expect(serious.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)).toEqual([]);
        }
      });
    }
  }
}
