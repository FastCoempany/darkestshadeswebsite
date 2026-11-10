/** The build this wall runs: the git commit's short hash, with "-dirty" when the tree had uncommitted changes, stamped
 * by vite.config.ts at build time so a phone's debug log (the `start` line) and the records panel say which build they
 * run; "dev" where nothing stamped it (a test import). */
declare const __WALL_BUILD__: string | undefined;
export const WALL_BUILD: string = typeof __WALL_BUILD__ === 'string' ? __WALL_BUILD__ : 'dev';
