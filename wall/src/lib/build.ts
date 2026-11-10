/** The build this wall runs: the git commit's short hash, with "-dirty" when the tree had uncommitted changes, stamped
 * by vite.config.ts at build time so a phone's debug log (the `start` line) and the records panel say which build they
 * run; empty where nothing stamped it (a test import, or a tree without git), and the panel then shows no line, as a
 * missing value renders nothing anywhere on the wall. */
declare const __WALL_BUILD__: string | undefined;
export const WALL_BUILD: string = typeof __WALL_BUILD__ === 'string' ? __WALL_BUILD__ : '';
