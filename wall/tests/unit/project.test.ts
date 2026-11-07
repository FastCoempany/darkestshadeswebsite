import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// D1: the project is wired. The logic tests (resolve, machine, gestures, spring, tier, the adapter) arrive in D2.
describe('the project', () => {
  it('pins every dependency to an exact version', () => {
    const pkg = JSON.parse(readFileSync(resolve(__dirname, '../../package.json'), 'utf8'));
    for (const [name, version] of Object.entries<string>(pkg.devDependencies)) {
      expect(version, name).toMatch(/^\d+\.\d+\.\d+$/);
    }
    expect(pkg.dependencies).toBeUndefined();
  });

  it('has the scripts the run names', () => {
    const pkg = JSON.parse(readFileSync(resolve(__dirname, '../../package.json'), 'utf8'));
    for (const s of ['dev', 'build', 'preview', 'test', 'test:e2e', 'check', 'lighthouse', 'assets', 'all']) {
      expect(pkg.scripts[s], s).toBeTruthy();
    }
  });
});
