import {useEffect, useState} from 'react';
import {cx} from '~/lib/cx';
import {formatRemaining, remaining} from '~/lib/time';

export interface CountdownProps {
  /** The real start or end time from drop data, or null: renders nothing. */
  to: string | null | undefined;
  /** The clock at render (ISO), so server and client agree on the first frame. */
  now: string;
  label: string;
  /** Called once when the time is reached, so the state can switch. */
  onReached?: () => void;
  className?: string;
}

/** Counts to a real time, stops at zero, never resets, never loops, never invents a time. */
export function Countdown({to, now, label, onReached, className}: CountdownProps) {
  const [current, setCurrent] = useState(() => new Date(now));
  const left = remaining(to ?? null, current);

  useEffect(() => {
    // Stories and screenshot runs are still (window.__dsStatic): the clock does not tick.
    if (!to || (window as Window & {__dsStatic?: boolean}).__dsStatic) return;
    const id = window.setInterval(() => setCurrent(new Date()), 1000);
    return () => window.clearInterval(id);
  }, [to]);

  useEffect(() => {
    if (to && !remaining(to, current)) onReached?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [to, left === null]);

  if (!to || !left) return null;
  return (
    <p className={cx('font-text text-small text-ds-text-secondary', className)} data-countdown>
      <span>{label} </span>
      <time dateTime={to} className="ds-tabular text-ds-text-primary">
        {formatRemaining(left)}
      </time>
    </p>
  );
}
