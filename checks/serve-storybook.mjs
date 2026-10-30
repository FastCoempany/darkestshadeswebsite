#!/usr/bin/env node
// Serve the static Storybook for the Playwright matrix, building it first when storybook-static/ is missing.
import {existsSync} from 'node:fs';
import {spawnSync, spawn} from 'node:child_process';

const ROOT = new URL('..', import.meta.url).pathname;
if (!existsSync(`${ROOT}/storybook-static/index.json`)) {
  const build = spawnSync('npm', ['run', 'storybook:build'], {cwd: ROOT, stdio: 'inherit'});
  if (build.status !== 0) process.exit(build.status ?? 1);
}
const server = spawn('npx', ['http-server', 'storybook-static', '-p', '6006', '-s', '-c-1'], {cwd: ROOT, stdio: 'inherit'});
server.on('exit', (code) => process.exit(code ?? 0));
