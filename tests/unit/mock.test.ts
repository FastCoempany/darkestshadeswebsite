import {describe, expect, it} from 'vitest';
import {createStore, effectiveState, store} from '~/lib/mock';
import {dropAnnouncedWithDate, dropEnded, dropLive} from '~/lib/mock/fixtures';
import {parseCsv} from '~/lib/mock/csv';

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
  it('reads every manifest row', () => {
    expect(store.images.all()).toHaveLength(65);
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
      '/photography/ds-f01-a1-640.avif 640w, /photography/ds-f01-a1-960.avif 960w, /photography/ds-f01-a1-1440.avif 1440w, /photography/ds-f01-a1-2048.avif 2048w',
    );
    expect(a1.url).toBe('/photography/ds-f01-a1-2048.jpg');
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
  it('knows the twenty planned pictures: nine finals, eleven drafts', () => {
    const shots = store.cast.shots();
    expect(shots).toHaveLength(20);
    expect(shots.filter((s) => s.status === 'final')).toHaveLength(9);
    expect(shots.filter((s) => s.status === 'draft')).toHaveLength(11);
  });

  it('maps a final to its manifest id without the version', () => {
    const w1 = store.cast.shots().find((s) => s.code === 'W1-S07-F02-A1')!;
    expect(w1.manifestId).toBe('ds-cast-w1-s07-f02');
    expect(w1.image?.ds.shot).toBe('W1-S07-F02-A1');
    const w2 = store.cast.shots().find((s) => s.code === 'W2-S06-F09-A2')!;
    expect(w2.image?.ds.manifestId).toBe('ds-cast-w2-s06-f09-a2');
  });

  it('gives every person a portrait slot; M3 and W3 stay drafts', () => {
    const members = store.cast.members();
    expect(members.map((m) => m.id)).toEqual(['W1', 'W2', 'W3', 'M1', 'M2', 'M3', 'NB']);
    expect(members.find((m) => m.id === 'W3')?.portrait?.status).toBe('draft');
    expect(members.find((m) => m.id === 'M3')?.portrait?.image).toBeNull();
    expect(members.find((m) => m.id === 'M1')?.portrait?.image?.ds.manifestId).toBe('ds-cast-m1-s06-f04');
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
