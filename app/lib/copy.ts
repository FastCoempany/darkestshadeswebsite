/**
 * The copy accessor. Every string the interface shows comes from content/copy/en.json (CLAUDE.md).
 * `fill` substitutes `{placeholders}`; it returns null when any value is missing, so a sentence that
 * needs a fact the data does not have renders nothing (docs/brief/08-copy.md, honesty rules).
 */
import en from '../../content/copy/en.json';

export const copy = en;
export type Copy = typeof en;
export type CopySection = Exclude<keyof Copy, '$comment'>;

export type Vars = Record<string, string | number | null | undefined>;

export function fill(template: string, vars: Vars = {}): string | null {
  let missing = false;
  const out = template.replace(/\{(\w+)\}/g, (_, key: string) => {
    const v = vars[key];
    if (v === null || v === undefined || v === '') {
      missing = true;
      return '';
    }
    return String(v);
  });
  return missing ? null : out;
}

/** The page title in the brand's template: "Frames · Darkest Shades". */
export function pageTitle(page?: string | null): string {
  return page ? (fill(en.meta.titleTemplate, {page}) ?? en.meta.brand) : en.meta.brand;
}

/**
 * A route's `meta`: the title from the template and a description, the site's own when the page has none.
 * React Router keeps only the leaf's descriptors, so every route sets both.
 */
export function pageMeta(page?: string | null, description?: string | null): {title?: string; name?: string; content?: string}[] {
  return [{title: pageTitle(page)}, {name: 'description', content: description ?? en.meta.defaultDescription}];
}

/** The Instagram profile, from the handle in the copy. */
export function instagramUrl(): string {
  return `https://instagram.com/${en.meta.instagram.replace(/^@/, '')}`;
}

export type CopyStatus = 'draft' | 'placeholder' | 'approved' | 'unknown';

/** A section's sign-off status. Sections without one count as draft (RUN.md). */
export function sectionStatus(section: CopySection): CopyStatus {
  const value = en[section] as unknown;
  if (typeof value !== 'object' || value === null) return 'unknown';
  const status = (value as {status?: unknown}).status;
  if (status === undefined) return 'draft';
  if (status === 'draft' || status === 'placeholder' || status === 'approved') return status;
  return 'unknown';
}

/** Sections that block a production build. Mirrors checks/lib/copy-status.mjs. */
export function blockingSections(): CopySection[] {
  return (Object.keys(en) as (keyof Copy)[])
    .filter((k): k is CopySection => !k.startsWith('$'))
    .filter((k) => sectionStatus(k) !== 'approved');
}
