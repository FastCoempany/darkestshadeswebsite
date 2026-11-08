import { describe, it, expect, vi } from 'vitest';
import { SequencePlayer } from '../../src/lib/sequence-player';
import { enableLog, log, logText, problem } from '../../src/lib/log';

// The shared pieces that have no DOM: the sequence player's window and ordering, the log.
function fakeBitmap(i: number): ImageBitmap {
  return { width: 10, height: 10, close: vi.fn(), __i: i } as unknown as ImageBitmap;
}

describe('SequencePlayer', () => {
  const frames = Array.from({ length: 24 }, (_, i) => ({ avif: `f${i}.avif`, webp: `f${i}.webp` }));
  const make = (opts: { avif?: boolean } = {}) => {
    const fetched: string[] = [];
    const decoded: number[] = [];
    const player = new SequencePlayer(frames, {
      avif: opts.avif ?? true,
      fetcher: async (url) => { fetched.push(url); return new Blob([url]); },
      decoder: async (blob) => { const i = Number((await blob.text()).match(/\d+/)![0]); decoded.push(i); return fakeBitmap(i); },
    });
    return { player, fetched, decoded };
  };

  it('fetches the first and the last frames first, in AVIF where it decodes', async () => {
    const { player, fetched } = make();
    await player.prefetch();
    expect(fetched[0]).toBe('f0.avif');
    expect(fetched[1]).toBe('f23.avif');
    expect(fetched).toHaveLength(24);
  });

  it('falls back to WebP', async () => {
    const { player, fetched } = make({ avif: false });
    await player.prefetch();
    expect(fetched.every((u) => u.endsWith('.webp'))).toBe(true);
  });

  it('holds at most the window of decoded frames and closes the rest', async () => {
    const { player, decoded } = make();
    await player.prefetch();
    player.seek(0.5);                 // frame 11.5: decodes 12, 13, 14 ahead and 11 behind
    await new Promise((r) => setTimeout(r, 10));
    expect(player.held()).toBeLessThanOrEqual(5);
    player.seek(0.0);
    await new Promise((r) => setTimeout(r, 10));
    expect(player.held()).toBeLessThanOrEqual(5);
    expect(decoded.length).toBeGreaterThan(0);
    for (const i of [11, 12, 13, 14]) expect(decoded).toContain(i);
  });

  it('seeks to the two neighbouring frames and their blend', () => {
    const { player } = make();
    expect(player.seek(0)).toEqual({ a: 0, b: 1, mix: 0 });
    expect(player.seek(1)).toEqual({ a: 23, b: 23, mix: 0 });
    const mid = player.seek(0.5);
    expect(mid.a).toBe(11);
    expect(mid.b).toBe(12);
    expect(mid.mix).toBeCloseTo(0.5);
    expect(player.seek(2).a).toBe(23);
    expect(player.seek(-1).a).toBe(0);
  });

  it('logs a failed fetch and keeps going', async () => {
    const events: string[] = [];
    const player = new SequencePlayer(frames.slice(0, 3), { avif: true, fetcher: async (u) => { if (u === 'f1.avif') throw new Error('nope'); return new Blob([u]); }, decoder: async () => fakeBitmap(0), onLog: (t) => events.push(t) });
    await player.prefetch();
    expect(events).toContain('sequence.fetch-failed');
    expect(await player.bitmap(1)).toBeNull();
    expect(await player.bitmap(0)).not.toBeNull();
  });

  it('dispose closes everything and answers null after', async () => {
    const { player } = make();
    await player.prefetch();
    await player.bitmap(0);
    player.dispose();
    expect(player.held()).toBe(0);
    expect(await player.bitmap(0)).toBeNull();
  });
});

describe('the event log', () => {
  it('keeps nothing until enabled, then events as text', () => {
    enableLog(false);
    log('x');
    expect(logText()).toBe('');
    enableLog(true);
    log('open', { frame: 'F09' });
    problem('drawer_bay/x: no frame');
    const text = logText();
    expect(text).toMatch(/\topen\t\{"frame":"F09"\}/);
    expect(text).toMatch(/\tproblem\t/);
    enableLog(false);
    expect(logText()).toBe('');
  });
});
