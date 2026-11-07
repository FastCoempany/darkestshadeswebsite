// The schema check: the records (data/wall.json against data/wall.schema.json) and the asset manifest
// (assets/manifest.json against assets/manifest.schema.json) validate. A data file without its schema fails.
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const WALL = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PAIRS = [
  ['data/wall.json', 'data/wall.schema.json'],
  ['assets/manifest.json', 'assets/manifest.schema.json'],
];
const ajv = new Ajv({ allErrors: true, strict: true, allowUnionTypes: true });
addFormats(ajv);
let failures = 0, checked = 0;
for (const [dataRel, schemaRel] of PAIRS) {
  const data = resolve(WALL, dataRel), schema = resolve(WALL, schemaRel);
  if (!existsSync(data)) { console.log(`schema: ${dataRel} not there yet`); continue; }
  if (!existsSync(schema)) { console.error(`schema: ${dataRel} has no schema at ${schemaRel}`); failures++; continue; }
  const validate = ajv.compile(JSON.parse(readFileSync(schema, 'utf8')));
  const ok = validate(JSON.parse(readFileSync(data, 'utf8')));
  checked++;
  if (!ok) {
    failures++;
    for (const e of validate.errors ?? []) console.error(`schema: ${dataRel}${e.instancePath} ${e.message}`);
  } else console.log(`schema: ${dataRel} validates against ${schemaRel}`);
}
console.log(`schema: ${checked} files validated, ${failures} failures`);
process.exit(failures ? 1 : 0);
