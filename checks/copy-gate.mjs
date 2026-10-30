#!/usr/bin/env node
// The draft-copy gate (docs/brief/09-build-plan.md): no draft or placeholder copy reaches a production
// build. The same function runs inside the Vite build (vite.config.ts); this script reports the state.
//   node checks/copy-gate.mjs            lists the sections that still block a production build (exit 0)
//   node checks/copy-gate.mjs --strict   exits 1 while any section blocks (what `npm run build` does)
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {blockingSections} from './lib/copy-status.mjs';

const ROOT = new URL('..', import.meta.url).pathname;
const copy = JSON.parse(readFileSync(join(ROOT, 'content/copy/en.json'), 'utf8'));
const blocking = blockingSections(copy);
const strict = process.argv.includes('--strict');
if (blocking.length) {
  const msg = `[copy-gate] ${blocking.length} section(s) of content/copy/en.json are not approved: ${blocking.join(', ')}.`;
  if (strict) {
    console.error(`${msg}\n[copy-gate] A production build refuses until the founder signs them off. Review builds: npm run build:review.`);
    process.exit(1);
  }
  console.log(`${msg}\n[copy-gate] A production build (npm run build) refuses; the review build (npm run build:review) allows them.`);
} else {
  console.log('[copy-gate] ok: every copy section is approved; a production build may ship it.');
}
