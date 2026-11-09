// The wall's switches (DRAWER-WALL.md, On a phone; D7): ?mech=pull, ?panel=1, ?debug=1 and ?open=<frame id or handle>
// in the query, as the plan names them, and the same as plain names in the hash, because the phone link is a published
// Artifact (O18) and an Artifact's link passes only a plain #name to the page, never a query string: #pull, #panel,
// #debug, #open-f09, joined with hyphens for more than one (#pull-debug). The hash's open takes the frame's id (f09), not
// its handle: handles are hyphenated and the hash splits on hyphens. A query value that names a switch wins both ways
// (?mech=tap beside #pull is tap first; ?debug=0 beside #debug keeps the log off).
export interface Flags {
  mech: 'tap' | 'pull';
  panel: boolean;
  debug: boolean;
  /** The frame to open on its last frame: an id or a handle as the query gives it; from the hash, the token after
   * `open`, lower-cased, which can only be an id. */
  open: string | null;
  /** How each switch was set, for the event log. */
  from: { query: string[]; hash: string[] };
}

export function readFlags(search: string, hash: string): Flags {
  const q = new URLSearchParams(search);
  const names = hash.replace(/^#/, '').split('-').map((s) => s.trim().toLowerCase()).filter(Boolean);
  const flags: Flags = { mech: 'tap', panel: false, debug: false, open: null, from: { query: [], hash: [] } };
  for (let i = 0; i < names.length; i++) {
    const n = names[i]!;
    if (n === 'pull') { flags.mech = 'pull'; flags.from.hash.push('mech'); }
    else if (n === 'panel') { flags.panel = true; flags.from.hash.push('panel'); }
    else if (n === 'debug') { flags.debug = true; flags.from.hash.push('debug'); }
    else if (n === 'open' && names[i + 1]) { flags.open = names[++i]!; flags.from.hash.push('open'); }
  }
  if (q.has('mech')) { flags.mech = q.get('mech') === 'pull' ? 'pull' : 'tap'; flags.from.query.push('mech'); }
  if (q.has('panel')) { flags.panel = q.get('panel') === '1'; flags.from.query.push('panel'); }
  if (q.has('debug')) { flags.debug = q.get('debug') === '1'; flags.from.query.push('debug'); }
  const open = q.get('open');
  if (open) { flags.open = open; flags.from.query.push('open'); }
  return flags;
}
