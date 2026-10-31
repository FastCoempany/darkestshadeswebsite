import {afterEach, describe, expect, it} from 'vitest';
import {cleanup, render, screen} from '@testing-library/react';

afterEach(cleanup);
import {Countdown} from '~/components/house/Countdown';
import {DropLine, dropLineText} from '~/components/house/DropLine';
import {DropStatus, dropSentence} from '~/components/house/DropStatus';
import {PairsLeft, pairsLeftText} from '~/components/house/PairsLeft';
import {availabilityWord, StageCard} from '~/components/house/StageCard';
import {specRows} from '~/components/house/SpecSheet';
import {toDropView} from '~/lib/drop-view';
import {store} from '~/lib/mock';
import {dropAnnouncedNoDate, dropAnnouncedWithDate, dropEnded, dropLive, dropSoldOut, inventoryLive, inventorySoldOut} from '~/lib/mock/fixtures';
import {createMemoryRouter, MemoryRouter, RouterProvider} from 'react-router';

/** DropStatus revalidates through the router when a countdown ends, so it renders inside a data router. */
function withRouter(ui: React.ReactElement) {
  return render(<RouterProvider router={createMemoryRouter([{path: '*', element: ui}])} />);
}

const NOW = new Date('2027-03-01T18:00:00Z');
const view = (d: typeof dropLive, inventory: Record<string, number> | null = null, threshold: number | null = null) => toDropView(d, NOW, inventory as never, threshold)!;

/** Honesty is enforced in code (05): these render nothing for a missing value, and never a made-up number. */
describe('PairsLeft', () => {
  it('renders nothing without inventory', () => {
    expect(pairsLeftText({left: null})).toBeNull();
    expect(pairsLeftText({left: undefined})).toBeNull();
    expect(pairsLeftText({left: Number.NaN})).toBeNull();
    const {container} = render(<PairsLeft left={null} total={120} />);
    expect(container.innerHTML).toBe('');
  });
  it('says the count with and without a total', () => {
    expect(pairsLeftText({left: 37, total: 120})).toBe('37 of 120 pairs left');
    expect(pairsLeftText({left: 37, total: null})).toBe('37 pairs left');
    expect(pairsLeftText({left: 0, total: 15})).toBe('0 of 15 pairs left');
  });
  it('hides the count above the founder’s threshold, and only then', () => {
    expect(pairsLeftText({left: 37, total: 120, threshold: 20})).toBeNull();
    expect(pairsLeftText({left: 12, total: 120, threshold: 20})).toBe('12 of 120 pairs left');
    expect(pairsLeftText({left: 37, total: 120, threshold: null})).toBe('37 of 120 pairs left');
  });
});

describe('Countdown', () => {
  it('renders nothing without a time, or once the time has passed', () => {
    const none = render(<Countdown to={null} now={NOW.toISOString()} label="Opens in" />);
    expect(none.container.innerHTML).toBe('');
    const past = render(<Countdown to="2027-02-01T00:00:00Z" now={NOW.toISOString()} label="Opens in" />);
    expect(past.container.innerHTML).toBe('');
    const bad = render(<Countdown to="not a time" now={NOW.toISOString()} label="Opens in" />);
    expect(bad.container.innerHTML).toBe('');
    const undef = render(<Countdown to={undefined} now={NOW.toISOString()} label="Opens in" />);
    expect(undef.container.innerHTML).toBe('');
  });
  it('counts to the real start', () => {
    render(<Countdown to={dropAnnouncedWithDate.startsAt} now={NOW.toISOString()} label="Opens in" />);
    expect(screen.getByText('Opens in')).toBeTruthy();
    expect(screen.getByText('3d 06:00:00')).toBeTruthy();
  });
});

describe('DropStatus', () => {
  it('renders nothing without a drop', () => {
    const {container} = withRouter(<DropStatus drop={null} />);
    expect(container.innerHTML).toBe('');
  });
  it("today's data: announced, no date, no numbers, no countdown", () => {
    const d = view(dropAnnouncedNoDate);
    expect(dropSentence(d)).toBe('Drop 001. Date to be announced.');
    withRouter(<DropStatus drop={d} />);
    expect(screen.queryByText(/pairs/)).toBeNull();
    expect(document.querySelector('[data-countdown]')).toBeNull();
  });
  it('announced with a date: the date, the time, the zone, a countdown', () => {
    const d = view(dropAnnouncedWithDate);
    expect(dropSentence(d)).toBe('Drop 001. March 4, 2027, 6:00 PM CST.');
    withRouter(<DropStatus drop={d} />);
    expect(document.querySelector('[data-countdown]')).not.toBeNull();
    expect(screen.queryByText(/pairs/)).toBeNull();
  });
  it('live with inventory: pairs per frame, in all, left, and the close countdown', () => {
    const d = view(dropLive, inventoryLive);
    withRouter(<DropStatus drop={d} />);
    expect(screen.getByText('15 pairs per frame · 120 pairs in all')).toBeTruthy();
    expect(screen.getByText('62 of 120 pairs left')).toBeTruthy();
    expect(screen.getByText('Closes in')).toBeTruthy();
  });
  it('live without inventory: no count at all', () => {
    const d = view({...dropLive, pairsPerFrame: null}, null);
    withRouter(<DropStatus drop={d} />);
    expect(screen.queryByText(/pairs/)).toBeNull();
  });
  it('live with the pairs made known but inventory unknown: the made count, no pairs left', () => {
    withRouter(<DropStatus drop={view(dropLive, null)} />);
    expect(screen.getByText('15 pairs per frame · 120 pairs in all')).toBeTruthy();
    expect(screen.queryByText(/pairs left/)).toBeNull();
  });
  it('a partial inventory is no total', () => {
    const partial = {...inventoryLive} as Record<string, number>;
    delete partial.F09;
    expect(view(dropLive, partial).pairsLeft).toBeNull();
    expect(view(dropLive, inventoryLive).pairsLeft).toBe(62);
  });
  it('sold out and ended: the sentence, nothing to count down to', () => {
    withRouter(<DropStatus drop={view(dropSoldOut, inventorySoldOut)} />);
    expect(screen.getByText('Drop 001 is sold out.')).toBeTruthy();
    expect(document.querySelector('[data-countdown]')).toBeNull();
    withRouter(<DropStatus drop={view(dropEnded, inventorySoldOut)} />);
    expect(screen.getByText('Drop 001 has ended.')).toBeTruthy();
  });
});

describe('DropLine', () => {
  it('is hidden without a drop, and when a drop has ended or sold out', () => {
    expect(dropLineText(null)).toBeNull();
    expect(dropLineText(view(dropEnded, inventorySoldOut))).toBeNull();
    expect(dropLineText(view(dropSoldOut, inventorySoldOut))).toBeNull();
    const {container} = render(<MemoryRouter><DropLine drop={null} /></MemoryRouter>);
    expect(container.innerHTML).toBe('');
  });
  it('shows only real numbers', () => {
    expect(dropLineText(view(dropAnnouncedNoDate))).toBe('Drop 001. Date to be announced.');
    expect(dropLineText(view(dropAnnouncedWithDate))).toBe('Drop 001 · March 4, 2027');
    expect(dropLineText(view(dropLive, inventoryLive))).toBe('Drop 001 · Open · 62 of 120 pairs left');
    expect(dropLineText(view(dropLive, null))).toBe('Drop 001 is open.');
    expect(dropLineText(view(dropLive, inventoryLive, 20))).toBe('Drop 001 is open.');
    expect(dropLineText(view(dropLive, inventoryLive, 100))).toBe('Drop 001 · Open · 62 of 120 pairs left');
  });
});

describe('the availability word and the spec sheet', () => {
  const f01 = store.products.byId('F01')!;
  const f06 = store.products.byId('F06')!;
  it('says In Drop, Sold out or Next drop from the data', () => {
    expect(availabilityWord(f01, view(dropAnnouncedNoDate))).toBe('In Drop 001');
    expect(availabilityWord(f01, view(dropLive, inventoryLive))).toBe('In Drop 001');
    expect(availabilityWord(store.products.byId('F02')!, view(dropLive, inventoryLive))).toBe('Sold out');
    expect(availabilityWord(f01, view(dropSoldOut, inventorySoldOut))).toBe('Sold out');
    expect(availabilityWord(f01, view(dropEnded, inventorySoldOut))).toBe('Next drop');
    expect(availabilityWord(f01, view({...dropLive, frames: ['F02']}, inventoryLive))).toBe('Next drop');
    expect(availabilityWord(f01, null)).toBeNull();
  });
  it('a stage card shows pairs left only while live, only for a frame in the inventory', () => {
    const live = view(dropLive, inventoryLive);
    render(<MemoryRouter><StageCard product={f01} drop={live} /></MemoryRouter>);
    expect(screen.getByText('7 of 15 pairs left')).toBeTruthy();
    cleanup();
    render(<MemoryRouter><StageCard product={f01} drop={view(dropAnnouncedWithDate)} /></MemoryRouter>);
    expect(screen.queryByText(/pairs left/)).toBeNull();
    cleanup();
    const partial = {...inventoryLive} as Record<string, number>;
    delete partial.F01;
    render(<MemoryRouter><StageCard product={f01} drop={view(dropLive, partial)} /></MemoryRouter>);
    expect(screen.queryByText(/pairs left/)).toBeNull();
  });
  it('leaves out rows whose value is null and never invents one', () => {
    const labels = specRows(f06).map((r) => r.label);
    expect(labels).not.toContain('Bridge');
    expect(specRows(f01).find((r) => r.label === 'Bridge')?.value).toBe('22 mm');
    expect(specRows(f06).find((r) => r.label === 'Size')?.value).toBe('139□— 150');
  });
});
