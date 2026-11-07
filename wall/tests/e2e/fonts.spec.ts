import { test, expect } from '@playwright/test';

// Before any screenshot: each type role has a loaded FontFace at every weight it uses (brand/fonts/README.md,
// Checks). The display role is Owners Wide 500 or its stand-in Mona Sans; the text role Stolzl 300/350/400/500 or
// its stand-in Urbanist. The kit's names owners-wide and stolzl count as the real fonts. Browsers load a face only
// when something uses it, so the test asks for each role's faces through document.fonts.load() and then checks
// what loaded. Fails on system type.
const PAGES = ['index.html', 'states.html'];
const ROLES = {
  display: { families: ['Owners Wide', 'owners-wide', 'Mona Sans Variable'], weights: [500] },
  text: { families: ['Stolzl', 'stolzl', 'Urbanist Variable'], weights: [300, 350, 400, 500] },
};

for (const page of PAGES) {
  test(`fonts load on ${page}`, async ({ page: p }) => {
    await p.goto(page);
    const report = await p.evaluate(async (roles) => {
      await document.fonts.ready;
      const out: Record<string, { loaded: string[]; ok: boolean; missing: number[] }> = {};
      for (const [role, { families, weights }] of Object.entries(roles)) {
        const loaded = new Set<string>();
        const missing: number[] = [];
        for (const weight of weights) {
          let covered = false;
          for (const family of families) {
            const faces = await document.fonts.load(`${weight} 16px "${family}"`).catch(() => []);
            for (const f of faces) {
              if (f.status !== 'loaded') continue;
              loaded.add(`${f.family.replace(/^["']|["']$/g, '')} ${f.weight}`);
              covered = true;
            }
          }
          if (!covered) missing.push(weight);
        }
        out[role] = { loaded: [...loaded], ok: missing.length === 0, missing };
      }
      return { display: out.display, text: out.text, body: getComputedStyle(document.body).fontFamily };
    }, ROLES);
    test.info().annotations.push({ type: 'fonts', description: `display: ${report.display?.loaded.join(', ') || 'none'}; text: ${report.text?.loaded.join(', ') || 'none'}; body stack: ${report.body}` });
    expect(report.display?.ok, `the display role has a loaded face at 500 (loaded: ${report.display?.loaded.join(', ') || 'none'})`).toBe(true);
    expect(report.text?.ok, `the text role has loaded faces at 300, 350, 400 and 500 (loaded: ${report.text?.loaded.join(', ') || 'none'}; missing ${report.text?.missing.join(', ')})`).toBe(true);
  });
}
