#!/usr/bin/env node
// Every content/products/f0X.json validates against content/products/product.schema.json.
import {readdirSync, readFileSync} from 'node:fs';
import {join} from 'node:path';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

const ROOT = new URL('..', import.meta.url).pathname;
const DIR = join(ROOT, 'content/products');
const schema = JSON.parse(readFileSync(join(DIR, 'product.schema.json'), 'utf8'));
const ajv = new Ajv2020({allErrors: true, strict: false});
addFormats(ajv);
const validate = ajv.compile(schema);

const files = readdirSync(DIR).filter((f) => /^f0\d\.json$/.test(f)).sort();
let bad = 0;
for (const f of files) {
  const data = JSON.parse(readFileSync(join(DIR, f), 'utf8'));
  if (!validate(data)) {
    bad++;
    console.error(`[check:schema] ${f}:`);
    for (const e of validate.errors) console.error(`    ${e.instancePath || '/'} ${e.message}`);
  }
}
if (bad) process.exit(1);
console.log(`[check:schema] ok: ${files.length} product files match product.schema.json (${files.join(', ')})`);
