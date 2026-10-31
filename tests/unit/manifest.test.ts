import {describe, expect, it} from 'vitest';
import {imagesFromManifest} from '~/lib/mock/manifest';
import {store} from '~/lib/mock';

const HEADER = 'id,source,frame,angle,version,width,height,widths,formats,tool_chain,master,master_location,status,alt,crop';

/** Phase 5 (RUN.md): the site reads MANIFEST.csv, so a new or replaced final needs no code change. */
describe('the manifest is the image library', () => {
  it('turns a new product row into the picture, its responsive set and its alt text', () => {
    const csv = `${HEADER}\nds-f05-a3,IMG_0001,F05,A3,v02,3000,3750,640 960,avif webp jpg,tools/photo/clean_lightbox.py,DS-F05-A3-v02-master.png,dam/product/,final,"Puffy square sunglasses, side view, on a light grey background.",0 0 3000 3750\n`;
    const [a3] = imagesFromManifest(csv);
    expect(a3.ds.shot).toBe('F05-A3');
    expect(a3.ds.kind).toBe('product');
    expect(a3.ds.status).toBe('final');
    expect(a3.altText).toBe('Puffy square sunglasses, side view, on a light grey background.');
    expect(a3.ds.formats).toEqual(['avif', 'webp', 'jpg']);
    expect(a3.ds.srcset.avif).toBe('/photography/ds-f05-a3-640.avif 640w, /photography/ds-f05-a3-960.avif 960w');
    expect(a3.ds.srcset.webp).toBe('/photography/ds-f05-a3-640.webp 640w, /photography/ds-f05-a3-960.webp 960w');
    expect(a3.url).toBe('/photography/ds-f05-a3-960.jpg');
    expect([a3.width, a3.height, a3.ds.ratioLabel]).toEqual([3000, 3750, '4:5']);
  });

  it('turns a cast row into the shot code the slots use', () => {
    const csv = `${HEADER}\nds-cast-m3-s02-f02,M3-S02-F02-A1,F02,A1,v01,2000,2500,640 960 1440,avif webp jpg,tools/photo/wear.py,DS-M3-S02-F02-A1-v01-master.png,dam/cast/,final,"A person in crimson tortoise sunglasses, facing the camera.",0 0 2000 2500\n`;
    const [m3] = imagesFromManifest(csv);
    expect(m3.ds.kind).toBe('cast');
    expect(m3.ds.shot).toBe('M3-S02-F02-A1');
    expect(m3.ds.frame).toBe('F02');
  });

  it('keeps a row for a frame the site does not sell out of the library', () => {
    const csv = `${HEADER}\nds-f07-a1,IMG_0002,F07,A1,v01,3000,3750,640,jpg,tools/photo/clean_lightbox.py,DS-F07-A1-v01-master.png,dam/product/,final,"Dropped frame.",0 0 3000 3750\n`;
    expect(imagesFromManifest(csv)).toEqual([]);
  });

  it('wires only the finals that reached main: nine cast pictures, five of them the portraits; the drafts stay labelled slots', () => {
    const shots = store.cast.shots();
    expect(shots.filter((s) => s.image).map((s) => s.code).sort()).toEqual([
      'M1-S06-F04-A1',
      'M1-S06-F08-A1',
      'M2-S07-F01-A1',
      'M2-S07-F05-A1',
      'NB-S06-F06-A1',
      'W1-S07-F02-A1',
      'W2-S06-F03-A1',
      'W2-S06-F03-A2',
      'W2-S06-F09-A2',
    ]);
    const slots = shots.filter((s) => !s.image).map((s) => s.code);
    expect(slots).toHaveLength(11);
    expect(slots).toContain('M3-S02-F02-A1');
    expect(slots).toContain('W3-S02-F09-A1');
    // One picture per person on /cast (RUN.md, Edge cases): the studio finals, M3 and W3 as labelled slots.
    expect(store.cast.members().map((m) => `${m.id}:${m.portrait?.image ? 'final' : 'slot'}`)).toEqual(['W1:final', 'W2:final', 'W3:slot', 'M1:final', 'M2:final', 'M3:slot', 'NB:final']);
  });

  it('counts every row of the committed manifest as a final today', () => {
    expect(store.images.all().every((i) => i.ds.status === 'final')).toBe(true);
    expect(store.images.all()).toHaveLength(65);
  });
});
