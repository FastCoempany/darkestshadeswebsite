// The draft-copy gate's one function, shared by checks/copy-gate.mjs, vite.config.ts and the unit test.
// A section of content/copy/en.json blocks a production build while its status is 'draft' or
// 'placeholder'. A section with no status counts as draft until the founder signs it off (RUN.md).

/** @param {Record<string, unknown>} copy @returns {string[]} the sections that block, with their status */
export function blockingSections(copy) {
  const out = [];
  for (const [section, value] of Object.entries(copy)) {
    if (section.startsWith('$') || typeof value !== 'object' || value === null) continue;
    const status = /** @type {{status?: unknown}} */ (value).status;
    if (status === 'draft' || status === 'placeholder') out.push(`${section} (${status})`);
    else if (status === undefined) out.push(`${section} (no status: counts as draft)`);
    else if (status !== 'approved') out.push(`${section} (unknown status "${String(status)}")`);
  }
  return out;
}
