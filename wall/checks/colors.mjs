// The colors check (CLAUDE.md, DRAWER-WALL.md): role tokens only in wall/src. No hex, rgb(), hsl() or named colors
// anywhere the wall ships a color: .css files; in .ts every css`` template, style attribute, string literal (a
// three.js `new Color('#…')`, a canvas fillStyle) and numeric literal (`0xffffff`); .svg files; <style> blocks and
// attributes in the pages. A scene color for the live frame comes from the tokens at run time, never from code.
// One allowance: the pages' <meta name="theme-color">, which cannot take a var(), must equal the surface-scene
// token's built value.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, resolve, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const WALL = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SCENE = JSON.parse(readFileSync(resolve(WALL, '../design/tokens/tokens.color.json'), 'utf8')).roles.night['surface-scene'].value.toLowerCase();
const NAMED = 'aliceblue|antiquewhite|aqua|aquamarine|azure|beige|bisque|black|blanchedalmond|blue|blueviolet|brown|burlywood|cadetblue|chartreuse|chocolate|coral|cornflowerblue|cornsilk|crimson|cyan|darkblue|darkcyan|darkgoldenrod|darkgray|darkgreen|darkgrey|darkkhaki|darkmagenta|darkolivegreen|darkorange|darkorchid|darkred|darksalmon|darkseagreen|darkslateblue|darkslategray|darkslategrey|darkturquoise|darkviolet|deeppink|deepskyblue|dimgray|dimgrey|dodgerblue|firebrick|floralwhite|forestgreen|fuchsia|gainsboro|ghostwhite|gold|goldenrod|gray|green|greenyellow|grey|honeydew|hotpink|indianred|indigo|ivory|khaki|lavender|lavenderblush|lawngreen|lemonchiffon|lightblue|lightcoral|lightcyan|lightgoldenrodyellow|lightgray|lightgreen|lightgrey|lightpink|lightsalmon|lightseagreen|lightskyblue|lightslategray|lightslategrey|lightsteelblue|lightyellow|lime|limegreen|linen|magenta|maroon|mediumaquamarine|mediumblue|mediumorchid|mediumpurple|mediumseagreen|mediumslateblue|mediumspringgreen|mediumturquoise|mediumvioletred|midnightblue|mintcream|mistyrose|moccasin|navajowhite|navy|oldlace|olive|olivedrab|orange|orangered|orchid|palegoldenrod|palegreen|paleturquoise|palevioletred|papayawhip|peachpuff|peru|pink|plum|powderblue|purple|rebeccapurple|red|rosybrown|royalblue|saddlebrown|salmon|sandybrown|seagreen|seashell|sienna|silver|skyblue|slateblue|slategray|slategrey|snow|springgreen|steelblue|tan|teal|thistle|tomato|turquoise|violet|wheat|white|whitesmoke|yellow|yellowgreen';
const RULES = [
  [/^theme-color .* is not the surface-scene token/, 'a theme-color off the token', false],
  [/#[0-9a-f]{3,8}\b/i, 'a hex color', false],
  [/\b(rgb|rgba|hsl|hsla|hwb|lab|lch|oklab|oklch|color)\s*\(/i, 'a literal color function', false],
  [new RegExp(`(^|[:\\s,('"])(${NAMED})(?=[\\s;,)!}'"]|$)`, 'i'), 'a named color', true],   // CSS and markup only
];

function* walk(dir) {
  if (!existsSync(dir)) return;
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else if (/\.(ts|js|mjs|css|html|svg)$/.test(name)) yield p;
  }
}

/** Where a color could hide: all of a .css or .svg file; in .ts/.js every css`...` template, every string literal and
 * every numeric hex literal; in .html every <style> block and every attribute value (the theme-color meta aside). */
// Each piece comes with `css: true` where it is CSS or markup (named colors count there too) or `css: false` for a
// plain string or number in code (hex and color functions count; a word like the knob style "gold" does not).
function cssOf(file, text) {
  const ext = extname(file);
  if (ext === '.css' || ext === '.svg') return [[0, text, true]];
  const out = [];
  if (ext === '.html') {
    for (const m of text.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/gi)) out.push([m.index, m[1], true]);
    for (const m of text.matchAll(/<meta\s+name="theme-color"\s+content="([^"]*)"/gi)) {
      if (m[1].toLowerCase() !== SCENE) out.push([m.index, `theme-color ${m[1]} is not the surface-scene token ${SCENE}`, true]);
    }
    const rest = text.replace(/<meta\s+name="theme-color"[^>]*>/gi, (t) => ' '.repeat(t.length));
    for (const m of rest.matchAll(/\s[a-z-]+\s*=\s*("[^"]*"|'[^']*')/gi)) out.push([m.index, m[1], true]);
    return out;
  }
  // .ts / .js: css`` and html`` templates and style attributes are CSS; other strings and numbers are code
  for (const m of text.matchAll(/\b(css|html|svg)`((?:[^`\\]|\\.)*)`/g)) out.push([m.index, m[2], true]);
  for (const m of text.matchAll(/\.style\.(?:setProperty|cssText)\s*\(\s*(['"`][^'"`]*['"`])/g)) out.push([m.index, m[1], true]);
  for (const m of text.matchAll(/`((?:[^`\\]|\\.)*)`/g)) out.push([m.index, m[1], false]);
  for (const m of text.matchAll(/'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"/g)) out.push([m.index, m[1] ?? m[2] ?? '', false]);
  for (const m of text.matchAll(/\b0x[0-9a-f]{6}\b|\b0x[0-9a-f]{8}\b|\b0x[0-9a-f]{3}\b/gi)) out.push([m.index, `#${m[0].slice(2)}`, false]);
  return out;
}

const files = [...walk(join(WALL, 'src')), join(WALL, 'index.html'), join(WALL, 'states.html')].filter(existsSync);
let failures = 0;
for (const file of files) {
  const text = readFileSync(file, 'utf8');
  for (const [offset, css, isCss] of cssOf(file, text)) {
    // comments and url() contents carry no colors
    const clean = css.replace(/\/\*[\s\S]*?\*\//g, (c) => ' '.repeat(c.length)).replace(/url\([^)]*\)/g, (u) => ' '.repeat(u.length));
    for (const [re, what, cssOnly] of RULES) {
      if (cssOnly && !isCss) continue;
      const m = clean.match(re);
      if (m) {
        failures++;
        const line = text.slice(0, offset + (m.index ?? 0)).split('\n').length;
        console.error(`colors: ${file}:${line} has ${what}: "${m[0].trim()}" (role tokens only)`);
        break;
      }
    }
  }
}
console.log(`colors: ${files.length} files scanned, ${failures} literal colors`);
process.exit(failures ? 1 : 0);
