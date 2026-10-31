import {existsSync, readdirSync} from 'node:fs';
import {describe, expect, it} from 'vitest';
import {imagesFromManifest, inGalleryOrder} from '~/lib/mock/manifest';
import {store} from '~/lib/mock';

const HEADER = 'id,source,frame,angle,version,width,height,widths,formats,tool_chain,master,master_location,status,alt,crop';
const PRODUCT_ROW = 'ds-f05-a3,IMG_3520,F05,A3,v02,3000,3750,960 640,avif webp jpg,tools/photo/clean_lightbox.py,DS-F05-A3-v02-master.png,dam/product/,final,"Puffy square sunglasses, side view, on a light grey background.",0 0 3000 3750';
const CAST_ROW = 'ds-cast-m3-s02-f02,M3-S02-F02-A1,F02,A1,v01,2000,2500,640 960 1440,avif webp jpg,tools/photo/wear.py; tools/photo/export_web.py,DS-CAST-M3-S02-F02-A1-v01-master.png,dam/people/,final,"A person in crimson tortoise sunglasses, facing the camera.",0 0 2000 2500';

/** Phase 5 (RUN.md): the site reads MANIFEST.csv, so a new or replaced final needs no code change. */
describe('the manifest is the image library', () => {
  it('turns a new product row into the picture, its responsive sets and its alt text; the version is the cache key', () => {
    const [a3] = imagesFromManifest(`${HEADER}\n${PRODUCT_ROW}\n`);
    expect(a3.ds.shot).toBe('F05-A3');
    expect(a3.ds.kind).toBe('product');
    expect(a3.altText).toBe('Puffy square sunglasses, side view, on a light grey background.');
    expect(a3.ds.widths).toEqual([640, 960]);
    expect(a3.ds.formats).toEqual(['avif', 'webp', 'jpg']);
    expect(a3.ds.srcset.avif).toBe('/photography/ds-f05-a3-640.avif?v=v02 640w, /photography/ds-f05-a3-960.avif?v=v02 960w');
    expect(a3.ds.srcset.webp).toBe('/photography/ds-f05-a3-640.webp?v=v02 640w, /photography/ds-f05-a3-960.webp?v=v02 960w');
    expect(a3.ds.srcset.jpg).toBe('/photography/ds-f05-a3-640.jpg?v=v02 640w, /photography/ds-f05-a3-960.jpg?v=v02 960w');
    expect(a3.url).toBe('/photography/ds-f05-a3-960.jpg?v=v02');
    expect([a3.width, a3.height, a3.ds.ratioLabel]).toEqual([3000, 3750, '4:5']);
  });

  it('turns a cast row into the shot code the slots use', () => {
    const [m3] = imagesFromManifest(`${HEADER}\n${CAST_ROW}\n`);
    expect(m3.ds.kind).toBe('cast');
    expect(m3.ds.shot).toBe('M3-S02-F02-A1');
    expect(m3.ds.frame).toBe('F02');
  });

  it('keeps a draft row and a row for a frame it does not sell out of the library', () => {
    const draft = PRODUCT_ROW.replace(',final,', ',draft,');
    const dropped = PRODUCT_ROW.replace('ds-f05-a3', 'ds-f07-a3').replace(',F05,', ',F07,');
    expect(imagesFromManifest(`${HEADER}\n${draft}\n${dropped}\n`)).toEqual([]);
  });

  it('puts an angle it does not know after the hero, never first', () => {
    const a7 = PRODUCT_ROW.replace('ds-f05-a3', 'ds-f05-a7').replace(',A3,', ',A7,');
    const h = PRODUCT_ROW.replace('ds-f05-a3', 'ds-f05-h').replace(',A3,', ',H,').replace('3000,3750', '3750,3000');
    const a1 = PRODUCT_ROW.replace('ds-f05-a3', 'ds-f05-a1').replace(',A3,', ',A1,');
    const ordered = inGalleryOrder(imagesFromManifest(`${HEADER}\n${a7}\n${h}\n${PRODUCT_ROW}\n${a1}\n`));
    expect(ordered.map((i) => i.ds.angle)).toEqual(['A1', 'A3', 'H', 'A7']);
  });

  it('names a missing column instead of failing somewhere else', () => {
    const header = HEADER.replace('widths', 'sizes');
    expect(() => imagesFromManifest(`${header}\n${PRODUCT_ROW}\n`)).toThrow(/missing the column\(s\) widths/);
    expect(imagesFromManifest('')).toEqual([]);
  });

  it('wires the finals that reached main and keeps every draft a labelled slot', () => {
    // One picture per person on /cast (RUN.md, Edge cases): the studio final when it exists, the labelled slot until then.
    for (const m of store.cast.members()) {
      expect(m.portrait).not.toBeNull();
      expect(m.portrait!.image !== null).toBe(m.portrait!.status === 'final');
    }
    for (const s of store.cast.shots()) expect(s.image !== null).toBe(s.status === 'final');
    const library = store.images.all();
    expect(library.every((i) => i.ds.status === 'final')).toBe(true);
    for (const i of library.filter((i) => i.ds.kind === 'product')) expect(['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'H']).toContain(i.ds.angle);
  });

  it('agrees with the folder: every file the manifest names exists, and every file in the folder is named', () => {
    const dir = 'assets/photography';
    const named = new Set<string>();
    for (const i of store.images.all()) {
      for (const f of i.ds.formats) {
        for (const w of i.ds.widths) {
          const file = `${i.ds.manifestId}-${w}.${f}`;
          expect(existsSync(`${dir}/${file}`), `${file} is in the manifest but not in ${dir}`).toBe(true);
          named.add(file);
        }
      }
    }
    const onDisk = readdirSync(dir).filter((f) => !['MANIFEST.csv', 'README.md'].includes(f) && !f.startsWith('.'));
    const orphans = onDisk.filter((f) => !named.has(f));
    expect(orphans, `files in ${dir} the manifest does not name`).toEqual([]);
    expect(named.size).toBeGreaterThan(0);
  });
});
