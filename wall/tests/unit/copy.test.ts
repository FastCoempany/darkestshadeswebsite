import { describe, it, expect, vi } from 'vitest';
import { t, missingKeys, subjectOf, stageAlt, brand } from '../../src/lib/copy';

// The copy reader: every string from the deck's wall section, placeholders filled, nothing made up for a key the
// deck lacks (it renders empty and is reported once).
describe('t', () => {
  it('reads the wall section, nested keys and placeholders', () => {
    expect(t('title')).toBe('The frames');
    expect(t('notYet')).toBe('Not yet.');
    expect(t('announce.open', { name: 'What Stevie Saw' })).toBe('What Stevie Saw. The drawer is open.');
    expect(t('announce.photo', { name: 'X', n: 2, count: 4, alt: 'y' })).toBe('X, photograph 2 of 4: y');
    expect(t('model3dLabel', { subject: 'chunky black sunglasses' })).toBe('chunky black sunglasses, a view you can turn');
  });
  it('leaves an unknown placeholder as it is', () => {
    expect(t('announce.shut', { name: 'x' })).toBe('The drawer is shut.');
    expect(t('announce.open')).toBe('{name}. The drawer is open.');
  });
  it('renders nothing for a key the deck lacks, and reports it once', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(t('nope.nothing')).toBe('');
    expect(t('nope.nothing')).toBe('');
    expect(warn).toHaveBeenCalledTimes(1);
    expect(missingKeys()).toContain('nope.nothing');
    warn.mockRestore();
  });
});

describe('alt and brand', () => {
  it('gives each frame its alt phrase, capitalised where it starts a sentence', () => {
    expect(subjectOf({ id: 'F09' })).toBe('chunky black sunglasses with thick rims');
    expect(subjectOf({ id: 'F09' }, true)).toBe('Chunky black sunglasses with thick rims');
    expect(subjectOf(null)).toBe('');
    expect(stageAlt({ id: 'F01' }, 'A1')).toBe('Blue tortoise navigator sunglasses with light blue lenses, front view, on a light grey background.');
  });
  it('carries the brand names from the deck', () => {
    expect(brand).toEqual({ brand: 'Darkest Shades', instagram: '@darkestshades', domain: 'darkestshades.com', hashtag: '#DarkestShades' });
  });
});
