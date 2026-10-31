import {mkdirSync, readFileSync} from 'node:fs';
import {expect, test} from '@playwright/test';
import {settle} from '../e2e/helpers';

/**
 * The review sets (09-build-plan.md): every page at 390 and 1440 as PNG, in wire mode to docs/wireframes/
 * (phase 1) or in UI mode to docs/ui/ (phase 4), plus every page state from the Storybook "Pages" stories.
 * Runs only when DS_CAPTURE is set: `DS_CAPTURE=wire npx playwright test --project=capture`.
 */
const MODE = (process.env.DS_CAPTURE === 'ui' ? 'ui' : 'wire') as 'ui' | 'wire';
const OUT = MODE === 'wire' ? 'docs/wireframes' : 'docs/ui';
const APP = 'http://localhost:3000';
const STORYBOOK = 'http://localhost:6006';

const PAGES: [string, string][] = [
  ['home', '/'],
  ['drop', '/drops/001'],
  ['frames', '/frames'],
  ['frame', '/frames/lou-went-underground'],
  ['frame-f08', '/frames/what-arnie-hid'],
  ['manifesto', '/manifesto'],
  ['cast', '/cast'],
  ['questions', '/questions'],
  ['care', '/care'],
  ['policies', '/policies'],
  ['policy-exchange', '/policies/exchange'],
  ['accessibility', '/accessibility'],
  ['bag', '/cart'],
  ['account', '/account'],
  ['not-found', '/this-page-does-not-exist'],
];

const SIZES = [
  {name: '390', width: 390, height: 844},
  {name: '1440', width: 1440, height: 900},
];

test.describe(`capture ${MODE}`, () => {
  test.beforeAll(() => {
    mkdirSync(OUT, {recursive: true});
    mkdirSync(`${OUT}/states`, {recursive: true});
  });

  for (const [slug, path] of PAGES) {
    for (const size of SIZES) {
      test(`${slug} @ ${size.name}`, async ({browser}) => {
        const context = await browser.newContext({viewport: {width: size.width, height: size.height}, deviceScaleFactor: 1, colorScheme: 'dark'});
        await context.addCookies([
          {name: 'ds_entry', value: 'seen', url: APP},
          {name: 'ds_offer', value: 'closed', url: APP},
          ...(MODE === 'wire' ? [{name: 'ds_mode', value: 'wire', url: APP}] : []),
        ]);
        const page = await context.newPage();
        // Captures are still: no clocks, no scroll-driven cuts.
        await page.addInitScript(() => {
          (window as Window & {__dsStatic?: boolean}).__dsStatic = true;
        });
        const response = await page.goto(`${APP}${path}`);
        expect(response?.status(), `${path} responds`).toBeLessThan(500);
        await settle(page);
        await page.screenshot({path: `${OUT}/${slug}-${size.name}.png`, fullPage: true});
        await context.close();
      });
    }
  }

  type Entry = {id: string; title: string; name: string; type: string};
  const index = JSON.parse(readFileSync('storybook-static/index.json', 'utf8')) as {entries: Record<string, Entry>};
  const states = Object.values(index.entries).filter((e) => e.type === 'story' && e.title.startsWith('Pages/'));
  for (const story of states) {
    for (const size of SIZES) {
      test(`state ${story.title} / ${story.name} @ ${size.name}`, async ({browser}) => {
        const context = await browser.newContext({viewport: {width: size.width, height: size.height}, deviceScaleFactor: 1, colorScheme: 'dark'});
        const page = await context.newPage();
        await page.goto(`${STORYBOOK}/iframe.html?id=${story.id}&viewMode=story&globals=mode:${MODE}`);
        // Storybook marks the body once the story has rendered; a story may legitimately render nothing.
        await page.waitForSelector('body.sb-show-main', {state: 'attached'});
        await settle(page);
        const slug = story.id.replace(/^pages-/, '');
        // Overlays (the menu, the bag drawer, the pop-up, the notice) are what the viewport shows; pages are captured whole.
        await page.screenshot({path: `${OUT}/states/${slug}-${size.name}.png`, fullPage: !story.title.startsWith('Pages/Overlays')});
        await context.close();
      });
    }
  }
});
