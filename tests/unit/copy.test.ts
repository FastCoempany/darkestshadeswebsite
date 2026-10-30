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
