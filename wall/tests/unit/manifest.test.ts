import { describe, it, expect } from 'vitest';
import { AssetIndex, isManifest, sequenceId, type Manifest } from '../../src/lib/manifest';
import manifestJson from '../../assets/manifest.json';

const entry = (id: string, kind: Manifest['assets'][number]['kind'], files: string[], over: Partial<Manifest['assets'][number]> = {}) =>
  ({ id, kind, files, status: 'mockup' as const, tool: 't', command: 'c', sourceCommit: 'abcdef0', ...over });

const sample: Manifest = {
  renderSet: 'wall-v1',
  assets: [
    entry('wall/portrait/black-relief/plate-lit', 'wall-plate', ['wall/portrait/black-relief/plate-lit.avif', 'wall/portrait/black-relief/plate-lit.webp'], { layout: 'portrait', knob: 'black-relief', width: 1170 }),
    entry('wall/portrait/black-relief/rects', 'rects', ['wall/portrait/black-relief/rects.json'], { layout: 'portrait', knob: 'black-relief' }),
    entry('wall/portrait/black-relief/bay-03-dark', 'wall-dark', ['wall/portrait/black-relief/bay-03-dark.avif'], { layout: 'portrait', knob: 'black-relief' }),
    entry(sequenceId('F09', 720, 0), 'sequence-frame', ['seq/F09/720/000.avif', 'seq/F09/720/000.webp'], { frame: 'F09', width: 720 }),
    entry(sequenceId('F09', 720, 1), 'sequence-frame', ['seq/F09/720/001.avif'], { frame: 'F09', width: 720 }),
    entry(sequenceId('F09', 1200, 0), 'sequence-frame', ['seq/F09/1200/000.avif'], { frame: 'F09', width: 1200 }),
    entry(sequenceId('base', 720, 0), 'sequence-frame', ['seq/base/720/000.avif']),
    entry('glb/F09', 'glb', ['glb/F09.glb'], { frame: 'F09' }),
    entry('stills/F01-lifted', 'still', ['stills/F01-lifted.avif'], { frame: 'F01' }),
    entry('env/drawer', 'env', ['env/drawer.hdr']),
    entry('camera/open', 'camera', ['camera/open.json']),
    entry('lens-tints', 'tints', ['lens-tints.json']),
  ],
};

describe('AssetIndex', () => {
  const idx = new AssetIndex(sample, '/x/');
  it('finds the plate, the rects and a dark crop by layout and knob', () => {
    expect(idx.plate('portrait', 'black-relief')?.id).toBe('wall/portrait/black-relief/plate-lit');
    expect(idx.plate('landscape', 'black-relief')).toBeNull();
    expect(idx.rects('portrait', 'black-relief')?.files[0]).toBe('wall/portrait/black-relief/rects.json');
    expect(idx.darkCrop('portrait', 'black-relief', 3)?.id).toBe('wall/portrait/black-relief/bay-03-dark');
    expect(idx.darkCrop('portrait', 'black-relief', 4)).toBeNull();
  });
  it('lists a sequence in order, per width, and the widths it exists at', () => {
    expect(idx.sequence('F09', 720).map((e) => e.id)).toEqual(['seq/F09/720/000', 'seq/F09/720/001']);
    expect(idx.sequence('F09', 1200)).toHaveLength(1);
    expect(idx.sequence('F01', 720)).toEqual([]);
    expect(idx.sequenceWidths('F09')).toEqual([720, 1200]);
    expect(idx.sequenceWidths('base')).toEqual([720]);
  });
  it('answers the resolver: a sequence to open, a GLB or a still to lift', () => {
    expect(idx.hasSequence('F09')).toBe(true);
    expect(idx.hasSequence('F01')).toBe(false);
    expect(idx.hasLift('F09')).toBe(true);     // the GLB
    expect(idx.hasLift('F01')).toBe(true);     // the still
    expect(idx.hasLift('F02')).toBe(false);
  });
  it('picks a file by format and makes a URL from the base', () => {
    const e = idx.byId.get('seq/F09/720/000')!;
    expect(idx.file(e, 'webp')).toBe('seq/F09/720/000.webp');
    expect(idx.file(e, 'avif')).toBe('seq/F09/720/000.avif');
    expect(idx.file(e, 'jxl')).toBe('seq/F09/720/000.avif');
    expect(idx.url('glb/F09.glb')).toBe('/x/glb/F09.glb');
    expect(idx.file({ ...e, files: [] })).toBeNull();
  });
  it('finds the environment, the cameras and the tints', () => {
    expect(idx.env()?.files[0]).toBe('env/drawer.hdr');
    expect(idx.camera('open')?.id).toBe('camera/open');
    expect(idx.camera('inspect')).toBeNull();
    expect(idx.tints()?.id).toBe('lens-tints');
  });
  it('reports an id listed twice', () => {
    const twice = new AssetIndex({ renderSet: 'x', assets: [sample.assets[0]!, sample.assets[0]!] });
    expect(twice.problems).toEqual(['wall/portrait/black-relief/plate-lit: listed twice']);
  });
});

describe('the committed manifest', () => {
  it('is a manifest the loader takes', () => {
    expect(isManifest(manifestJson)).toBe(true);
    expect(isManifest({})).toBe(false);
    const idx = new AssetIndex(manifestJson as Manifest);
    expect(idx.problems).toEqual([]);
  });
});
