import {ENTRY_COOKIE, readCookie} from '~/lib/cookies';

/**
 * When the opening plays (docs/brief/03-references.md): the first visit to `/` only. Never on a deep
 * link (any other path, or a utm_*, fbclid or gclid parameter), for a returning visitor (the cookie),
 * or for a crawler. Reduced motion is handled in the player: cards only, no bursts.
 */
export function shouldShowEntry(request: Request, isBot: boolean): boolean {
  const url = new URL(request.url);
  if (url.pathname !== '/') return false;
  for (const key of url.searchParams.keys()) {
    if (key.startsWith('utm_') || key === 'fbclid' || key === 'gclid') return false;
  }
  if (isBot) return false;
  const seen = readCookie(request.headers.get('Cookie'), ENTRY_COOKIE);
  return seen !== 'seen' && seen !== 'off';
}

/** The cookie that remembers a finished or skipped opening for 30 days, or `off` from the Accessibility page. */
export function entryCookie(value: 'seen' | 'off' | 'on'): string {
  const maxAge = value === 'on' ? 0 : value === 'off' ? 60 * 60 * 24 * 365 : 60 * 60 * 24 * 30;
  return `${ENTRY_COOKIE}=${value === 'on' ? '' : value}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
}
