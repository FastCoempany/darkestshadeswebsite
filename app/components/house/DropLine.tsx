import {Link} from 'react-router';
import {dropSentence} from '~/components/house/DropStatus';
import type {DropView} from '~/lib/drop-view';
import {copy, fill} from '~/lib/copy';
import {cx} from '~/lib/cx';
import {formatDropTime} from '~/lib/time';

/**
 * One line under the header on every page while a drop is announced or live: "Drop 001 · Open · 37 of
 * 120 pairs left". Only real numbers; hidden when there is no drop or it has ended or sold out (04).
 */
export function DropLine({drop, inline = false}: {drop: DropView | null; inline?: boolean}) {
  const text = dropLineText(drop);
  if (!text) return null;
  const Tag = inline ? 'p' : 'div';
  return (
    <Tag className={cx('font-text text-micro font-medium uppercase tracking-micro text-ds-text-secondary', !inline && 'border-y border-ds-border-hairline px-4 py-2 text-center md:px-6')} data-drop-line>
      <Link to={`/drops/${drop!.number}`} className="hover:text-ds-text-primary hover:underline underline-offset-3">
        {text}
      </Link>
    </Tag>
  );
}

export function dropLineText(drop: DropView | null): string | null {
  if (!drop) return null;
  if (drop.state === 'ended' || drop.state === 'sold-out') return null;
  if (drop.state === 'live') {
    const left = drop.pairsLeft;
    const total = drop.pairsTotal;
    return fill(copy.drop.line.live, {number: drop.number, left, total}) ?? dropSentence(drop);
  }
  const when = formatDropTime(drop.startsAt, drop.timezone);
  return when ? fill(copy.drop.line.announced, {number: drop.number, date: when.date}) : fill(copy.drop.states.announcedNoDate, {number: drop.number});
}
