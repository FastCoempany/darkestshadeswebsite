/** Read one cookie from a Cookie header. */
export function readCookie(header: string | null, name: string): string | null {
  if (!header) return null;
  for (const part of header.split(';')) {
    const [k, ...rest] = part.trim().split('=');
    if (k === name) return decodeURIComponent(rest.join('='));
  }
  return null;
}

/** The entry's "seen" cookie: set for 30 days when the opening is skipped or finished (03-references.md). */
export const ENTRY_COOKIE = 'ds_entry';
/** Wire mode on the whole site: `ds_mode=wire` (phase 1 wireframes). */
export const MODE_COOKIE = 'ds_mode';
