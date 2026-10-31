import {describe, expect, it} from 'vitest';
import en from '../../content/copy/en.json';
import {blockingSections} from '../../checks/lib/copy-status.mjs';
import {blockingSections as appBlocking, copy, fill, pageTitle, sectionStatus} from '~/lib/copy';

describe('the draft-copy gate', () => {
  it("refuses today's en.json: sections are still draft or placeholder", () => {
    const blocking = blockingSections(en as Record<string, unknown>);
    expect(blocking.length).toBeGreaterThan(0);
    expect(blocking).toContain('care (placeholder)');
    expect(blocking).toContain('entry (draft)');
  });

  it('counts a section without a status as draft', () => {
    expect(blockingSections({nav: {drop: 'Drop'}})).toEqual(['nav (no status: counts as draft)']);
  });

  it('passes only when every section is approved', () => {
    expect(blockingSections({$comment: 'x', nav: {status: 'approved', drop: 'Drop'}})).toEqual([]);
    expect(blockingSections({nav: {status: 'approved'}, care: {status: 'placeholder'}})).toEqual(['care (placeholder)']);
  });

  it('agrees with the app-side accessor', () => {
    const fromChecks = blockingSections(en as Record<string, unknown>).map((s) => s.split(' ')[0]);
    expect(appBlocking()).toEqual(fromChecks);
    expect(sectionStatus('care')).toBe('placeholder');
    expect(sectionStatus('nav')).toBe('draft');
  });
});

describe('fill', () => {
  it('substitutes placeholders', () => {
    expect(fill(copy.drop.states.announcedNoDate, {number: '001'})).toBe('Drop 001. Date to be announced.');
  });
  it('returns null when a value is missing, so the sentence renders nothing', () => {
    expect(fill(copy.drop.pairsLeft, {left: 37, total: null})).toBeNull();
    expect(fill(copy.drop.pairsLeft, {left: 37})).toBeNull();
    expect(fill(copy.drop.pairsLeft, {left: 37, total: 120})).toBe('37 of 120 pairs left');
    expect(fill(copy.drop.pairsLeft, {left: 0, total: 120})).toBe('0 of 120 pairs left');
  });
  it('builds page titles from the template', () => {
    expect(pageTitle('Frames')).toBe('Frames · Darkest Shades');
    expect(pageTitle()).toBe('Darkest Shades');
  });
});

describe('page meta', () => {
  it('always ships a description: the page’s own, else the site’s', async () => {
    const {pageMeta, instagramUrl} = await import('~/lib/copy');
    expect(pageMeta()).toEqual([{title: 'Darkest Shades'}, {name: 'description', content: copy.meta.defaultDescription}]);
    expect(pageMeta('Cast')).toEqual([{title: 'Cast · Darkest Shades'}, {name: 'description', content: copy.meta.defaultDescription}]);
    expect(pageMeta('Frames', 'Eight frames.')[1]).toEqual({name: 'description', content: 'Eight frames.'});
    expect(pageMeta('Frames', null)[1].content).toBe(copy.meta.defaultDescription);
    expect(instagramUrl()).toBe('https://instagram.com/darkestshades');
  });

  it('fills a frame’s description from its data and the price', () => {
    expect(fill(copy.meta.frameDescription, {name: 'Lou Went Underground', descriptor: 'Blue navigator', price: '$100'})).toBe('Lou Went Underground. Blue navigator. $100. Released in drops.');
    expect(fill(copy.meta.frameDescription, {name: 'Lou Went Underground', descriptor: null, price: '$100'})).toBeNull();
  });
});

describe('the list’s sentence', () => {
  it('promises early access only when the store really gates the drop', async () => {
    const {listBody} = await import('~/lib/list-offer');
    expect(listBody()).toBe(copy.list.bodyNoEarlyAccess);
    expect(listBody({enabled: false, hours: 24})).toBe(copy.list.bodyNoEarlyAccess);
    expect(listBody({enabled: true, hours: null})).toBe(copy.list.bodyNoEarlyAccess);
    expect(listBody({enabled: true, hours: 24})).toBe(copy.list.body.replace('{hours}', '24'));
  });
});
