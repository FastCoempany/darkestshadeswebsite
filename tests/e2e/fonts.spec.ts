import {expect, test} from '@playwright/test';

/**
 * The font check (brand/fonts/README.md, Checks): each role has a loaded FontFace at every weight it
 * uses. Display: Owners Wide 500, or the Mona Sans stand-in. Text: Stolzl 300, 350, 400 and 500, or the
 * Urbanist stand-in. The kit's names (owners-wide, stolzl) count as the real fonts. System type fails.
 * `document.fonts.check()` alone cannot do this: it returns true when no @font-face exists at all.
 */
const DISPLAY = ['Owners Wide', 'owners-wide', 'Mona Sans Variable'];
const TEXT = ['Stolzl', 'stolzl', 'Urbanist Variable'];

type Face = {family: string; weight: string; status: string};

function covers(face: Face, weight: number): boolean {
  const parts = face.weight.replace(/normal/, '400').replace(/bold/, '700').split(/\s+/).map(Number);
  if (parts.length === 2) return weight >= parts[0] && weight <= parts[1];
  return parts[0] === weight;
}

test('both faces load for every role and weight; no system type renders the roles', async ({page}) => {
  await page.goto('/dev/tokens');
  await page.evaluate(() => document.fonts.ready);
  // Force every weight the site uses to load (variable fonts load per unicode range on demand).
  await page.evaluate(async () => {
    const loads = [
      document.fonts.load('500 16px "Mona Sans Variable"'),
      document.fonts.load('500 16px "Owners Wide"'),
      ...[300, 350, 400, 500].flatMap((w) => [document.fonts.load(`${w} 16px "Urbanist Variable"`), document.fonts.load(`${w} 16px "Stolzl"`)]),
    ];
    await Promise.allSettled(loads);
  });
  const faces: Face[] = await page.evaluate(() =>
    Array.from(document.fonts).map((f) => ({family: f.family.replace(/^["']|["']$/g, ''), weight: f.weight, status: f.status})),
  );
  const loaded = faces.filter((f) => f.status === 'loaded');
  const display = loaded.filter((f) => DISPLAY.includes(f.family));
  const text = loaded.filter((f) => TEXT.includes(f.family));

  const rendered: Record<string, string> = await page.evaluate(() =>
    Object.fromEntries(
      Array.from(document.querySelectorAll<HTMLElement>('[data-font-role]')).map((el) => [
        el.dataset.fontRole!,
        `${getComputedStyle(el).fontFamily} @ ${getComputedStyle(el).fontWeight}`,
      ]),
    ),
  );
  for (const [role, font] of Object.entries(rendered)) console.log(`[fonts] ${role}: ${font}`);
  console.log(`[fonts] display faces loaded: ${[...new Set(display.map((f) => `${f.family} ${f.weight}`))].join('; ')}`);
  console.log(`[fonts] text faces loaded: ${[...new Set(text.map((f) => `${f.family} ${f.weight}`))].join('; ')}`);

  expect(display.some((f) => covers(f, 500)), 'display face at 500').toBe(true);
  for (const w of [300, 350, 400, 500]) {
    expect(text.some((f) => covers(f, w)), `text face at ${w}`).toBe(true);
  }
  // Every role's first family in its stack is one of the two faces, never a system font.
  for (const [role, font] of Object.entries(rendered)) {
    const first = font.split(',')[0].replace(/^["']|["']$/g, '').trim();
    expect([...DISPLAY, ...TEXT], `${role} renders ${first}`).toContain(first);
  }
  expect(Object.keys(rendered).length).toBeGreaterThanOrEqual(10);
});
