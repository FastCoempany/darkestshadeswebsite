import type {Page} from '@playwright/test';

async function waitForImages(page: Page): Promise<void> {
  // Images outside the viewport (a swipe track's later slides) may never load lazily: wait briefly, then go on.
  await page.evaluate(() =>
    Promise.race([
      Promise.all(Array.from(document.images).filter((i) => !i.complete).map((i) => new Promise((r) => { i.onload = i.onerror = r; }))),
      new Promise((r) => setTimeout(r, 3000)),
    ]),
  );
}

/**
 * Scroll through the page so lazy images load and scroll-driven states (the scale cut) settle, then wait
 * for fonts, the network and the images before a screenshot. Repeats while the scroll reveals new images.
 */
export async function settle(page: Page): Promise<void> {
  let seen = -1;
  for (let round = 0; round < 3; round++) {
    await page.evaluate(async () => {
      const step = Math.max(200, Math.floor(window.innerHeight * 0.8));
      for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise((r) => setTimeout(r, 20));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => document.fonts.ready);
    await waitForImages(page);
    const count = await page.evaluate(() => document.images.length);
    if (count === seen) break;
    seen = count;
  }
}
