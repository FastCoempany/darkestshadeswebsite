// The local event log (DRAWER-WALL.md, Honesty and brand): no analytics, no third-party scripts. Behind ?debug=1 the
// wall keeps a log of its events in memory (and mirrors it to the console), for the tests and the usability
// sessions, which copy it at the end. Without the flag nothing is kept.

export interface LogEvent {
  t: number;
  type: string;
  data?: Record<string, unknown>;
}

const events: LogEvent[] = [];
let enabled = false;
const MAX = 5000;

export function enableLog(on: boolean): void {
  enabled = on;
  if (!on) events.length = 0;
}

export function logEnabled(): boolean {
  return enabled;
}

export function log(type: string, data?: Record<string, unknown>): void {
  if (!enabled) return;
  const e: LogEvent = { t: Math.round(performance.now()), type, ...(data ? { data } : {}) };
  events.push(e);
  if (events.length > MAX) events.splice(0, events.length - MAX);
  console.debug('[wall]', type, data ?? '');
}

export function events_(): readonly LogEvent[] {
  return events;
}

/** The log as text, one event a line, for the copy button. */
export function logText(): string {
  return events.map((e) => `${e.t}\t${e.type}${e.data ? '\t' + JSON.stringify(e.data) : ''}`).join('\n');
}

/** Problems the resolver and the adapter report go to the log and, always, to the console once. */
const seen = new Set<string>();
export function problem(message: string): void {
  if (!seen.has(message)) {
    seen.add(message);
    console.warn('[wall]', message);
  }
  log('problem', { message });
}
