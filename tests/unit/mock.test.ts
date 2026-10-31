import {describe, expect, it} from 'vitest';
import {createStore, effectiveState, store} from '~/lib/mock';
import {dropAnnouncedWithDate, dropEnded, dropLive} from '~/lib/mock/fixtures';
import {parseCsv} from '~/lib/mock/csv';
import manifestCsv from '../../assets/photography/MANIFEST.csv?raw';
import {readdirSync, readFileSync} from 'node:fs';

describe('products', () => {
  it('lists the eight frames by look number, with no 07', () => {
    const looks = store.products.all().map((p) => p.ds.lookNumber);
    expect(looks).toEqual(['01', '02', '03', '04', '05', '06', '08', '09']);
  });

  it('uses the names as handles in kebab case', () => {
    expect(store.products.byHandle('lou-went-underground')?.title).toBe('Lou Went Underground');
    expect(store.products.byHandle('what-stevie-saw')?.ds.descriptor).toBe('The blackout');
    expect(store.products.byHandle('nothing-here')).toBeNull();
  });

  it('prices every frame at $100 and never invents inventory', () => {
    for (const p of store.products.all()) {
      expect(p.priceRange.minVariantPrice).toEqual({amount: '100.00', currencyCode: 'USD'});
      expect(p.variants.nodes[0].quantityAvailable).toBeNull();
      expect(p.variants.nodes[0].compareAtPrice).toBeNull();
    }
  });

  it('keeps null facts null (F06 has no bridge)', () => {
    expect(store.products.byId('F06')?.ds.measurementsMm.bridge).toBeNull();
    expect(store.products.byId('F06')?.ds.sizeNotation).toBe('139□— 150');
    expect(store.products.byId('F01')?.ds.measurementsMm.bridge).toBe(22);
  });

  it('is not for sale while the drop is only announced', () => {
    expect(store.products.all().every((p) => !p.availableForSale)).toBe(true);
    expect(store.products.byId('F01')?.tags).toEqual(['look-01', 'drop-001']);
  });

  it('walks to the next look and wraps', () => {
    expect(store.products.next('F06')?.ds.id).toBe('F08');
    expect(store.products.next('F09')?.ds.id).toBe('F01');
  });
});

describe('images', () => {
  it('turns every final row for a frame it sells into a picture, and nothing else', () => {
    const sold = new Set(store.products.all().map((p) => p.ds.id));
    const rows = parseCsv(manifestCsv);
    const finals = rows.filter((r) => r.status === 'final' && sold.has(r.frame));
    expect(finals.length).toBeGreaterThan(0);
    expect(store.images.all().map((i) => i.ds.manifestId).sort()).toEqual(finals.map((r) => r.id).sort());
  });

  it('orders a frame gallery A1 to A6 then the hero', () => {
    expect(store.images.forFrame('F01').map((i) => i.ds.angle)).toEqual(['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'H']);
    expect(store.images.forFrame('F01')[0].ds.shot).toBe('F01-A1');
    expect(store.images.forFrame('F01')[6].ds.ratioLabel).toBe('3:2');
  });

  it('builds the responsive set from the widths column', () => {
    const a1 = store.images.byId('ds-f01-a1')!;
    expect(a1.ds.widths).toEqual([640, 960, 1440, 2048]);
    expect(a1.ds.srcset.avif).toBe(
      '/photography/ds-f01-a1-640.avif?v=v01 640w, /photography/ds-f01-a1-960.avif?v=v01 960w, /photography/ds-f01-a1-1440.avif?v=v01 1440w, /photography/ds-f01-a1-2048.avif?v=v01 2048w',
    );
    expect(a1.url).toBe('/photography/ds-f01-a1-2048.jpg?v=v01');
    expect(a1.altText).toMatch(/front view, on a light grey background\.$/);
  });

  it('keeps alt text with commas intact', () => {
    const rows = parseCsv('id,alt\nx,"a, b"\ny,plain\n');
    expect(rows).toEqual([
      {id: 'x', alt: 'a, b'},
      {id: 'y', alt: 'plain'},
    ]);
  });
});

describe('cast', () => {
  it('knows every planned picture: a final has its export, a draft stays a labelled slot', () => {
    const dir = 'content/photography/people';
    const planned = readdirSync(dir).filter((f) => f.endsWith('.json'));
    const files = Object.fromEntries(planned.map((f) => [f.replace(/\.json$/, ''), JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')) as {status: string}]));
    const shots = store.cast.shots();
    expect(shots.map((s) => s.code).sort()).toEqual(Object.keys(files).sort());
    for (const s of shots) {
      expect(s.status).toBe(files[s.code].status === 'final' ? 'final' : 'draft');
      expect(s.image !== null).toBe(s.status === 'final');
    }
    expect(shots.filter((s) => s.status === 'final').length).toBeGreaterThan(0);
  });

  it('maps a final to its manifest id without the version', () => {
    const w1 = store.cast.shots().find((s) => s.code === 'W1-S07-F02-A1')!;
    expect(w1.manifestId).toBe('ds-cast-w1-s07-f02');
    expect(w1.image?.ds.shot).toBe('W1-S07-F02-A1');
    const w2 = store.cast.shots().find((s) => s.code === 'W2-S06-F09-A2')!;
    expect(w2.image?.ds.manifestId).toBe('ds-cast-w2-s06-f09-a2');
  });

  it('gives every person a portrait: a picture when its export exists, a labelled slot until then', () => {
    const members = store.cast.members();
    expect(members.map((m) => m.id)).toEqual(['W1', 'W2', 'W3', 'M1', 'M2', 'M3', 'NB']);
    for (const m of members) {
      expect(m.portrait).not.toBeNull();
      expect(m.portrait!.image !== null).toBe(m.portrait!.status === 'final');
      if (m.portrait!.image) expect(m.portrait!.image.ds.manifestId).toBe(m.portrait!.manifestId);
    }
  });

  it('gives every frame at least one on-model final, F03 two', () => {
    for (const f of ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F08', 'F09'] as const) {
      expect(store.images.castForFrame(f).length).toBeGreaterThanOrEqual(1);
    }
    expect(store.images.castForFrame('F03')).toHaveLength(2);
  });
});

describe('drops', () => {
  it("shows Drop 001 as announced with no date and no numbers (today's data)", () => {
    const d = store.drops.current()!;
    expect(d.number).toBe('001');
    expect(d.state).toBe('announced');
    expect(d.startsAt).toBeNull();
    expect(d.pairsPerFrame).toBeNull();
    expect(d.limitPerCustomer).toBeNull();
    expect(d.earlyAccess.enabled).toBe(false);
    expect(d.statement).toBeNull();
  });

  it('switches state only on real times', () => {
    expect(effectiveState(dropAnnouncedWithDate, new Date('2027-03-01T00:00:00Z'))).toBe('announced');
    expect(effectiveState(dropAnnouncedWithDate, new Date('2027-03-05T00:00:00Z'))).toBe('live');
    expect(effectiveState(dropAnnouncedWithDate, new Date('2027-03-12T00:00:00Z'))).toBe('ended');
    expect(effectiveState(dropLive, new Date('2027-03-01T00:00:00Z'))).toBe('live');
    expect(effectiveState(dropEnded, new Date('2030-01-01T00:00:00Z'))).toBe('ended');
  });

  it('builds a store for a moment in time', () => {
    const later = createStore(new Date('2030-01-01T00:00:00Z'));
    expect(later.drops.current()?.state).toBe('announced');
  });
});
