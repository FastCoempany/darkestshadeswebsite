import {copy, fill} from '~/lib/copy';
import {cx} from '~/lib/cx';

export interface PairsLeftProps {
  /** Pairs left from inventory, or null: unknown, renders nothing. */
  left: number | null | undefined;
  /** Pairs made, or null: the sentence without a total. */
  total?: number | null;
  /** Above this many pairs the count is hidden; null means no threshold (the founder sets it). */
  threshold?: number | null;
  className?: string;
}

/** The sentence for a real remaining quantity, or nothing. Never a made-up number (docs/brief/05-components.md). */
export function pairsLeftText({left, total = null, threshold = null}: Omit<PairsLeftProps, 'className'>): string | null {
  if (left === null || left === undefined || !Number.isFinite(left) || left < 0) return null;
  if (threshold !== null && threshold !== undefined && left > threshold) return null;
  if (total !== null && total !== undefined && Number.isFinite(total)) return fill(copy.drop.pairsLeft, {left, total});
  return fill(copy.drop.pairsLeftNoTotal, {left});
}

export function PairsLeft(props: PairsLeftProps) {
  const text = pairsLeftText(props);
  if (!text) return null;
  return <p className={cx('ds-tabular font-text text-small text-ds-text-secondary', props.className)} data-pairs-left>{text}</p>;
}
