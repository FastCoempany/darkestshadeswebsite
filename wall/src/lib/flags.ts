// The wall's switches (DRAWER-WALL.md, On a phone; D7): ?mech=pull, ?panel=1, ?debug=1 and ?open=<frame> in the query,
// as the plan names them, and the same as plain names in the hash, because the phone link is a published Artifact
// (O18) and an Artifact's link passes only a plain #name to the page, never a query string: #pull, #panel, #debug,
// #open-f09, joined with hyphens for more than one (#pull-debug). The query wins where both name the same switch.
export interface Flags {
  mech: 'tap' | 'pull';
  panel: boolean;
  debug: boolean;
  /** The frame to open on its last frame (an id or a handle as the query gives it; the hash's token lower-cased). */
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
  if (q.get('mech') === 'pull') { flags.mech = 'pull'; flags.from.query.push('mech'); }
  if (q.get('panel') === '1') { flags.panel = true; flags.from.query.push('panel'); }
  if (q.get('debug') === '1') { flags.debug = true; flags.from.query.push('debug'); }
  const open = q.get('open');
  if (open) { flags.open = open; flags.from.query.push('open'); }
  return flags;
}
