import { describe, it, expect } from 'vitest';
import { readRecords, withRecord, listField, textField } from '../../src/data/adapter';
import { metaobject, recordsFile } from './fixtures';
import wallJson from '../../data/wall.json';

// The adapter: metaobject shape in, typed drawers out; missing values stay missing; broken references are reported.
describe('readRecords', () => {
  it('reads the committed records: one wall, eight drawers in look-number order, all available and auto', () => {
    const r = readRecords(wallJson);
    expect(r.problems).toEqual([]);
    expect(r.wall).toEqual({ id: 'bay_wall/frames', handle: 'frames', bays: ['drawer_bay/f01', 'drawer_bay/f02', 'drawer_bay/f03', 'drawer_bay/f04', 'drawer_bay/f05', 'drawer_bay/f06', 'drawer_bay/f08', 'drawer_bay/f09'], knobStyle: 'black-relief', renderSet: 'wall-v1' });
    expect(r.order.map((b) => b.frame)).toEqual(['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F08', 'F09']);
    expect(r.order.every((b) => b.state === 'available' && b.light === 'auto')).toBe(true);
  });

  it('types a drawer from its fields and leaves a missing field null', () => {
    const r = readRecords(recordsFile([{ frame: 'F03', state: 'sold_out' }]));
    expect(r.order[0]).toEqual({ id: 'drawer_bay/f03', handle: 'f03', frame: 'F03', state: 'sold_out', light: null, note: null });
  });

  it('keeps unknown values for the resolver to judge, without filling anything in', () => {
    const r = readRecords(recordsFile([{ frame: 'F07', state: 'soon', light: 'bright' }]));
    expect(r.order[0]).toMatchObject({ frame: 'F07', state: 'soon', light: 'bright' });
    expect(r.problems).toEqual([]);
  });

  it('reports a bays entry that points nowhere and leaves it out of the order', () => {
    const file = recordsFile([{ frame: 'F01', state: 'available' }], { bays: JSON.stringify(['drawer_bay/f01', 'drawer_bay/f02']) });
    const r = readRecords(file);
    expect(r.order).toHaveLength(1);
    expect(r.problems).toEqual(['bay_wall/frames: bays lists drawer_bay/f02, which is not a drawer_bay record']);
  });

  it('reports a bays value that is not JSON or not a list of ids', () => {
    expect(readRecords(recordsFile([], { bays: 'not json' })).problems).toContain('bay_wall/frames: bays is not JSON');
    expect(readRecords(recordsFile([], { bays: JSON.stringify([1, 2]) })).problems).toContain('bay_wall/frames: bays is not a list of ids');
  });

  it('reports no records, no wall, an unknown type, a record without an id, a drawer listed twice', () => {
    expect(readRecords({}).problems).toEqual(['no records', 'no bay_wall record with handle "frames"']);
    expect(readRecords({ records: [metaobject('drawer_bay/f01', 'drawer_bay', { frame: 'F01' })] }).problems).toEqual(['no bay_wall record with handle "frames"']);
    expect(readRecords({ records: [metaobject('x/y', 'other', {})] }).problems).toContain('x/y: unknown record type "other"');
    expect(readRecords({ records: [{ fields: [] }] }).problems).toContain('a record without an id or a type');
    const twice = recordsFile([{ frame: 'F01', state: 'available' }]);
    twice.records.push(twice.records[1]!);
    expect(readRecords(twice).problems).toContain('drawer_bay/f01: listed twice');
  });

  it('a drawer with no fields array is typed as all null', () => {
    const r = readRecords({ records: [metaobject('bay_wall/frames', 'bay_wall', { bays: '["drawer_bay/f01"]' }, { bays: 'list.metaobject_reference' }), { id: 'drawer_bay/f01', handle: 'f01', type: 'drawer_bay', fields: undefined as never }] });
    expect(r.order[0]).toEqual({ id: 'drawer_bay/f01', handle: 'f01', frame: null, state: null, light: null, note: null });
  });
});

describe('withRecord', () => {
  it('replaces one drawer and no other, keeping the wall order', () => {
    const r = readRecords(wallJson);
    const changed = withRecord(r, metaobject('drawer_bay/f04', 'drawer_bay', { frame: 'F04', state: 'locked', light: 'auto', note: 'x' }));
    expect(changed.bays.get('drawer_bay/f04')?.state).toBe('locked');
    expect(changed.order[3]?.state).toBe('locked');
    expect(changed.order.filter((b) => b.state === 'available')).toHaveLength(7);
    expect(r.bays.get('drawer_bay/f04')?.state).toBe('available');
  });
  it('ignores a record that is not a drawer', () => {
    const r = readRecords(wallJson);
    expect(withRecord(r, metaobject('bay_wall/frames', 'bay_wall', {}))).toBe(r);
  });
});

describe('field readers', () => {
  it('read text and list fields, tolerating absence', () => {
    const m = metaobject('drawer_bay/f01', 'drawer_bay', { frame: 'F01' });
    expect(textField(m, 'frame')).toBe('F01');
    expect(textField(m, 'state')).toBeNull();
    const problems: string[] = [];
    expect(listField(m, 'bays', problems)).toEqual([]);
    expect(problems).toEqual([]);
  });
});
