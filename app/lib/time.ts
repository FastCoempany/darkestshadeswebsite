/** Dates and times for drops, in the drop's own time zone (content/drops/*.json, `timezone`). */
export interface DropTime {
  /** "March 4, 2027" */
  date: string;
  /** "6:00 PM" */
  time: string;
  /** "CST" */
  timezone: string;
}

export function formatDropTime(iso: string | null, timeZone: string): DropTime | null {
  if (!iso) return null;
  const ms = Date.parse(iso);
  if (!Number.isFinite(ms)) return null;
  const d = new Date(ms);
  const date = new Intl.DateTimeFormat('en-US', {timeZone, month: 'long', day: 'numeric', year: 'numeric'}).format(d);
  const parts = new Intl.DateTimeFormat('en-US', {timeZone, hour: 'numeric', minute: '2-digit', timeZoneName: 'short'}).formatToParts(d);
  const time = parts
    .filter((p) => ['hour', 'minute', 'literal', 'dayPeriod'].includes(p.type))
    .map((p) => p.value)
    .join('')
    .trim()
    .replace(/\s+$/, '');
  const timezone = parts.find((p) => p.type === 'timeZoneName')?.value ?? '';
  return {date, time: time.replace(/,\s*$/, ''), timezone};
}

export interface Remaining {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  totalMs: number;
}

/** Time left until `iso`, or null when there is no real time or it has passed. */
export function remaining(iso: string | null, now: Date): Remaining | null {
  if (!iso) return null;
  const target = Date.parse(iso);
  if (!Number.isFinite(target)) return null;
  const totalMs = target - now.getTime();
  if (totalMs <= 0) return null;
  const s = Math.floor(totalMs / 1000);
  return {days: Math.floor(s / 86400), hours: Math.floor((s % 86400) / 3600), minutes: Math.floor((s % 3600) / 60), seconds: s % 60, totalMs};
}

/** "3d 04:12:09" in tabular figures; days only when there are any. */
export function formatRemaining(r: Remaining): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  const clock = `${pad(r.hours)}:${pad(r.minutes)}:${pad(r.seconds)}`;
  return r.days > 0 ? `${r.days}d ${clock}` : clock;
}
