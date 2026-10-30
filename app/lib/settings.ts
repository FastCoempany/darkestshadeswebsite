/** Site settings read from the environment. Nothing here is a fact about a product or a drop. */
export interface SiteSettings {
  /** Above this many pairs left, the count is hidden. null = no threshold: the founder decides (RUN.md, phase 3). */
  pairsLeftThreshold: number | null;
  /** Adobe Fonts web project id (brand/fonts/README.md, route A), or null for the stand-ins. */
  adobeFontsKit: string | null;
  /** Production settings with draft copy allowed (review build), or the dev server. */
  reviewBuild: boolean;
}

export function settingsFrom(env: Partial<Env> | undefined): SiteSettings {
  const raw = env?.PUBLIC_PAIRS_LEFT_THRESHOLD;
  const n = raw ? Number(raw) : NaN;
  return {
    pairsLeftThreshold: Number.isFinite(n) && n > 0 ? Math.floor(n) : null,
    adobeFontsKit: env?.PUBLIC_ADOBE_FONTS_KIT?.trim() || null,
    reviewBuild: env?.DS_REVIEW_BUILD === '1' || import.meta.env.DS_REVIEW_BUILD === '1',
  };
}
