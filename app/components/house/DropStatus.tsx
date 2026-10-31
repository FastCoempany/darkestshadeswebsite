import {useRevalidator} from 'react-router';
import {Countdown} from '~/components/house/Countdown';
import {PairsLeft} from '~/components/house/PairsLeft';
import {copy, fill} from '~/lib/copy';
import {cx} from '~/lib/cx';
import type {DropView} from '~/lib/drop-view';
import type {DropState} from '~/lib/mock/types';
import {formatDropTime} from '~/lib/time';

export type {DropView} from '~/lib/drop-view';
export {toDropView} from '~/lib/drop-view';

export function stateWord(state: DropState): string {
  return {announced: copy.drop.stateWords.announced, live: copy.drop.stateWords.live, 'sold-out': copy.drop.stateWords.soldOut, ended: copy.drop.stateWords.ended}[state];
}

/** The one sentence for the drop's state; with no date, "Date to be announced". */
export function dropSentence(drop: DropView): string {
  const when = formatDropTime(drop.startsAt, drop.timezone);
  switch (drop.state) {
    case 'announced':
      return (when && fill(copy.drop.states.announced, {number: drop.number, ...when})) ?? fill(copy.drop.states.announcedNoDate, {number: drop.number}) ?? '';
    case 'live':
      return fill(copy.drop.states.live, {number: drop.number}) ?? '';
    case 'sold-out':
      return fill(copy.drop.states.soldOut, {number: drop.number}) ?? '';
    case 'ended':
      return fill(copy.drop.states.ended, {number: drop.number}) ?? '';
  }
}

export interface DropStatusProps {
  drop: DropView | null;
  variant?: 'block' | 'small';
  className?: string;
}

/**
 * Drop number, state word, date and time with the time zone, pairs per frame and in all, pairs left,
 * and a countdown only to a real start or end. Renders nothing without a drop (docs/brief/05, 08).
 */
export function DropStatus({drop, variant = 'block', className}: DropStatusProps) {
  const revalidator = useRevalidator();
  if (!drop) return null;
  const sentence = dropSentence(drop);
  const perFrame = fill(copy.drop.pairsPerFrame, {pairs: drop.pairsPerFrame});
  const total = fill(copy.drop.pairsTotal, {total: drop.pairsTotal});
  const countdownTo = drop.state === 'announced' ? drop.startsAt : drop.state === 'live' ? drop.endsAt : null;
  const countdownLabel = drop.state === 'announced' ? copy.drop.countdownLabel.toStart : copy.drop.countdownLabel.toEnd;
  return (
    <div className={cx('grid content-start gap-3', variant === 'small' && 'text-center justify-items-center', className)} data-drop-status={drop.state}>
      <p className="font-text text-micro font-medium uppercase tracking-micro text-ds-text-secondary">
        <span className={cx(drop.state === 'live' && 'text-ds-status-live')}>{stateWord(drop.state)}</span>
      </p>
      <p className={cx('font-text text-ds-text-primary', variant === 'block' ? 'text-body-lg' : 'text-body')}>{sentence}</p>
      {variant === 'block' && (perFrame || total) ? (
        <p className="ds-tabular font-text text-small text-ds-text-secondary">{[perFrame, total].filter(Boolean).join(' · ')}</p>
      ) : null}
      <PairsLeft left={drop.pairsLeft} total={drop.pairsTotal} threshold={drop.threshold} />
      <Countdown to={countdownTo} now={drop.now} label={countdownLabel} onReached={() => void revalidator.revalidate()} />
    </div>
  );
}
