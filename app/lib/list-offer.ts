import {useEffect, useState} from 'react';
import {cookieFlags, readCookie} from '~/lib/cookies';
import {copy, fill} from '~/lib/copy';

export const OFFER_COOKIE = 'ds_offer';

/** The list's one sentence: early access only when the store really gates the drop (08-copy.md, 00-decisions.md O6). */
export function listBody(earlyAccess?: {enabled: boolean; hours: number | null}): string {
  return (earlyAccess?.enabled && earlyAccess.hours ? fill(copy.list.body, {hours: earlyAccess.hours}) : null) ?? copy.list.bodyNoEarlyAccess;
}

/** `closed`: 30 days. `joined`: a year (04, Overlays). */
export function offerCookie(value: 'closed' | 'joined', secure?: boolean): string {
  const maxAge = value === 'joined' ? 60 * 60 * 24 * 365 : 60 * 60 * 24 * 30;
  return `${OFFER_COOKIE}=${value}; Max-Age=${maxAge}; ${cookieFlags(secure)}`;
}

/**
 * Opens the list pop-up once per visitor, at 60% scroll, on the pages that enable it (home, drop, frame).
 * Never on the first screen, never while the opening plays (`<html data-opening="playing">`), never again
 * for 30 days after closing or a year after signing up.
 */
export function useListOffer(enabled: boolean): {open: boolean; close: () => void; joined: () => void} {
  const [open, setOpen] = useState(false);
  const [spent, setSpent] = useState(false);

  useEffect(() => {
    if (!enabled || spent) return;
    // Screenshot runs and stories are still: no pop-up on a scripted scroll.
    if ((window as Window & {__dsStatic?: boolean}).__dsStatic) return;
    if (readCookie(document.cookie, OFFER_COOKIE)) {
      setSpent(true);
      return;
    }
    const onScroll = () => {
      if (document.documentElement.dataset.opening === 'playing') return;
      const doc = document.documentElement;
      const max = doc.scrollHeight - window.innerHeight;
      if (max <= 0) return;
      const progress = window.scrollY / max;
      if (progress >= 0.6 && window.scrollY > window.innerHeight * 0.8) {
        setOpen(true);
        setSpent(true);
      }
    };
    window.addEventListener('scroll', onScroll, {passive: true});
    return () => window.removeEventListener('scroll', onScroll);
  }, [enabled, spent]);

  return {
    open,
    close: () => {
      // Closing after joining keeps the year-long cookie.
      if (readCookie(document.cookie, OFFER_COOKIE) !== 'joined') document.cookie = offerCookie('closed');
      setOpen(false);
    },
    joined: () => {
      document.cookie = offerCookie('joined');
    },
  };
}
