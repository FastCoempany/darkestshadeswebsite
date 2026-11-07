import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { copyFrom, frameFacts, framesFrom } from '../../src/data/extract';
import { FRAME_IDS } from '../../src/lib/types';

const PRODUCTS = resolve(__dirname, '../../../content/products');
const DECK = resolve(__dirname, '../../../content/copy/en.json');
const products = readdirSync(PRODUCTS).filter((f) => /^f0[1-9]\.json$/.test(f)).map((f) => JSON.parse(readFileSync(resolve(PRODUCTS, f), 'utf8')));
const deck = JSON.parse(readFileSync(DECK, 'utf8'));

describe('the frames the wall ships', () => {
  const frames = framesFrom(products);
  it('are the eight, each with its look number, name, handle and $100 from its record, and nothing else', () => {
    expect(Object.keys(frames).sort()).toEqual([...FRAME_IDS].sort());
    for (const id of FRAME_IDS) {
      const f = frames[id]!;
      expect(f.lookNumber).toMatch(/^0[1-9]$/);
      expect(f.name!.length).toBeGreaterThan(0);
      expect(f.handle).toMatch(/^[a-z-]+$/);
      expect(f.price).toEqual({ amount: '100.00', currencyCode: 'USD' });
      expect(Object.keys(f).sort()).toEqual(['handle', 'id', 'lookNumber', 'name', 'price']);
    }
  });
  it('matches 06-products.md: the look numbers and names', () => {
    expect(frames.F09).toMatchObject({ lookNumber: '09', name: 'What Stevie Saw', handle: 'what-stevie-saw' });
    expect(frames.F02).toMatchObject({ lookNumber: '02', name: 'Holly Wore Them to Breakfast' });
    expect(JSON.stringify(frames)).not.toMatch(/Founder|Oct 20|measurementsMm|placement/);   // no internal notes ship
  });
  it('leaves out what is not a frame and nulls what a record lacks, filling nothing in', () => {
    expect(frameFacts({ id: 'F07', name: 'x' })).toBeNull();
    expect(frameFacts(null)).toBeNull();
    expect(frameFacts({ id: 'F01' })).toEqual({ id: 'F01', handle: null, lookNumber: null, name: null, price: null });
    expect(frameFacts({ id: 'F01', price: { amount: 5, currencyCode: 'USD' } })!.price).toBeNull();
  });
});

describe('the copy the wall ships', () => {
  const copy = copyFrom(deck);
  const KEYS = ['title', 'openLabel', 'notYet', 'soldOut', 'hintPull', 'hintLift', 'hintTurn', 'open', 'shut', 'close', 'lift', 'putBack', 'photos', 'photosClose', 'turnLeft', 'turnRight', 'closer', 'further', 'reset', 'model3dLabel'];
  it('has every wall.* string DRAWER-WALL.md lists, as a draft', () => {
    expect(copy.wall.status).toBe('draft');
    for (const k of KEYS) expect(typeof copy.wall[k], k).toBe('string');
    const announce = copy.wall.announce as Record<string, string>;
    for (const k of ['open', 'shut', 'lifted', 'back']) expect(typeof announce[k], `announce.${k}`).toBe('string');
    expect(copy.wall.model3dLabel).toContain('{subject}');
    expect(announce.open).toContain('{name}');
  });
  it('has the alt phrases for the eight frames and the angles the zoom shows', () => {
    for (const id of FRAME_IDS) expect(copy.alt.subjects[id], id).toBeTruthy();
    for (const a of ['A1', 'A2', 'A3', 'A6']) expect(copy.alt.angles[a], a).toBeTruthy();
    expect(copy.alt.stage).toContain('{subject}');
  });
  it('carries the brand names and none of the site\'s sections', () => {
    expect(copy.meta).toEqual({ brand: 'Darkest Shades', instagram: '@darkestshades', domain: 'darkestshades.com', hashtag: '#DarkestShades' });
    expect(Object.keys(copy)).toEqual(['wall', 'alt', 'meta']);
    expect(JSON.stringify(copy)).not.toMatch(/checkout|bag|newsletter|manifesto/i);
  });
  it('uses no exclamation marks and no lorem ipsum', () => {
    const text = JSON.stringify(copy.wall);
    expect(text).not.toMatch(/!/);
    expect(text).not.toMatch(/lorem/i);
  });
});
