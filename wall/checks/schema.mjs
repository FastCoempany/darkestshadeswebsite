// The schema check: the records (data/wall.json against data/wall.schema.json) and the asset manifest
// (assets/manifest.json against assets/manifest.schema.json) validate. Both files are required; a data file without
// its schema fails.
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

const WALL = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PAIRS = [
  ['data/wall.json', 'data/wall.schema.json'],
  ['assets/manifest.json', 'assets/manifest.schema.json'],
];
const ajv = new Ajv2020({ allErrors: true, strict: true, allowUnionTypes: true });
addFormats(ajv);
let failures = 0, checked = 0;
for (const [dataRel, schemaRel] of PAIRS) {
  const data = resolve(WALL, dataRel), schema = resolve(WALL, schemaRel);
  if (!existsSync(data)) { console.error(`schema: ${dataRel} is missing`); failures++; continue; }
  if (!existsSync(schema)) { console.error(`schema: ${dataRel} has no schema at ${schemaRel}`); failures++; continue; }
  const validate = ajv.compile(JSON.parse(readFileSync(schema, 'utf8')));
  const ok = validate(JSON.parse(readFileSync(data, 'utf8')));
  checked++;
  if (!ok) {
    failures++;
    for (const e of validate.errors ?? []) console.error(`schema: ${dataRel}${e.instancePath} ${e.message}`);
  } else console.log(`schema: ${dataRel} validates against ${schemaRel}`);
}
// The records' cross-references: every id a bays list names is a drawer_bay record, no id is listed twice, every
// drawer's frame is a product in content/products/ (an unset frame is allowed: the resolver hides that drawer).
const recordsPath = resolve(WALL, 'data/wall.json');
if (existsSync(recordsPath)) {
  const { records } = JSON.parse(readFileSync(recordsPath, 'utf8'));
  const ids = new Map();
  for (const r of records) { if (ids.has(r.id)) { console.error(`schema: ${r.id} is listed twice`); failures++; } ids.set(r.id, r); }
  const products = new Set(readdirSync(resolve(WALL, '../content/products')).filter((f) => /^f0[1-9]\.json$/.test(f)).map((f) => f.slice(0, 3).toUpperCase()));
  for (const r of records) {
    const value = (key) => r.fields.find((f) => f.key === key)?.value ?? null;
    if (r.type === 'bay_wall') {
      const bays = JSON.parse(value('bays') ?? '[]');
      for (const id of bays) if (ids.get(id)?.type !== 'drawer_bay') { console.error(`schema: ${r.id} lists ${id}, which is not a drawer_bay record`); failures++; }
      if (new Set(bays).size !== bays.length) { console.error(`schema: ${r.id} lists a drawer twice`); failures++; }
    } else if (r.type === 'drawer_bay') {
      const frame = value('frame');
      if (frame !== null && !products.has(frame)) { console.error(`schema: ${r.id} names frame "${frame}", which is not in content/products/`); failures++; }
    }
  }
  console.log(`schema: ${records.length} records cross-checked (${products.size} products on disk)`);
}
console.log(`schema: ${checked} files validated, ${failures} failures`);
process.exit(failures ? 1 : 0);
