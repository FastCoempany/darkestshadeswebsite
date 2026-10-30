import {describe, expect, it} from 'vitest';
import {act, render, renderHook, screen} from '@testing-library/react';
import {toE164} from '~/components/base/Field';
import {Price} from '~/components/base/Price';
import {CartProvider, emptyCart, lineFor, useCart} from '~/lib/cart';
import {formatMoney} from '~/lib/money';
import {store} from '~/lib/mock';
import {formatDropTime, formatRemaining, remaining} from '~/lib/time';

describe('money', () => {
  it('shows $100 without cents and never hides the price', () => {
    expect(formatMoney({amount: '100.00', currencyCode: 'USD'})).toBe('$100');
    expect(formatMoney({amount: '200.00', currencyCode: 'USD'})).toBe('$200');
    expect(formatMoney({amount: '99.50', currencyCode: 'USD'})).toBe('$99.50');
    render(<Price money={{amount: '100.00', currencyCode: 'USD'}} />);
    expect(screen.getByText('$100')).toBeTruthy();
  });
});

describe('the bag', () => {
  it('builds a line in the cart API shape with the unit price and the line total', () => {
    const f01 = store.products.byId('F01')!;
    const line = lineFor(f01, f01.variants.nodes[0], 2);
    expect(line.merchandise.price.amount).toBe('100.00');
    expect(line.cost.totalAmount.amount).toBe('200.00');
    expect(line.merchandise.product).toMatchObject({handle: 'lou-went-underground', lookNumber: '01'});
    expect(emptyCart.totalQuantity).toBe(0);
    expect(emptyCart.checkoutUrl).toBeNull();
  });
});

describe('the bag honors the per-customer limit', () => {
  const f01 = store.products.byId('F01')!;
  const wrapper = ({children}: {children: React.ReactNode}) => <CartProvider persist={false}>{children}</CartProvider>;

  it('clamps a line to the limit and never below zero', () => {
    const {result} = renderHook(() => useCart(), {wrapper});
    act(() => result.current.add(lineFor(f01, f01.variants.nodes[0], 1), 2));
    act(() => result.current.add(lineFor(f01, f01.variants.nodes[0], 5), 2));
    expect(result.current.cart.lines.nodes).toHaveLength(1);
    expect(result.current.cart.lines.nodes[0].quantity).toBe(2);
    expect(result.current.cart.totalQuantity).toBe(2);
    expect(result.current.cart.cost.subtotalAmount.amount).toBe('200.00');
    expect(result.current.isOpen).toBe(true);
  });

  it('removes a line set to zero and sums the rest', () => {
    const f09 = store.products.byId('F09')!;
    const {result} = renderHook(() => useCart(), {wrapper});
    act(() => result.current.add(lineFor(f01, f01.variants.nodes[0], 1)));
    act(() => result.current.add(lineFor(f09, f09.variants.nodes[0], 2)));
    const first = result.current.cart.lines.nodes[0].id;
    act(() => result.current.setQuantity(first, 0));
    expect(result.current.cart.lines.nodes.map((l) => l.merchandise.product.lookNumber)).toEqual(['09']);
    expect(result.current.cart.cost.totalAmount.amount).toBe('200.00');
    act(() => result.current.remove(result.current.cart.lines.nodes[0].id));
    expect(result.current.cart.totalQuantity).toBe(0);
  });
});

describe('phone numbers', () => {
  it('composes E.164 from the country and the national number', () => {
    expect(toE164('(415) 555-0123', 'US')).toBe('+14155550123');
    expect(toE164('1 415 555 0123', 'US')).toBe('+14155550123');
    expect(toE164('06 1234 5678', 'IT')).toBe('+390612345678');
    expect(toE164('07700 900123', 'GB')).toBe('+447700900123');
    expect(toE164('+33 6 12 34 56 78', 'US')).toBe('+33612345678');
    expect(toE164('   ', 'US')).toBeNull();
  });
});

describe('time', () => {
  it('formats a drop time in the drop’s zone', () => {
    const t = formatDropTime('2027-03-04T18:00:00-06:00', 'America/Chicago')!;
    expect(t.date).toBe('March 4, 2027');
    expect(t.time).toMatch(/^6:00 PM/);
    expect(t.timezone).toBe('CST');
    expect(formatDropTime(null, 'America/Chicago')).toBeNull();
    expect(formatDropTime('not a date', 'America/Chicago')).toBeNull();
  });
  it('counts down only to a real future time', () => {
    const now = new Date('2027-03-01T12:00:00Z');
    expect(remaining(null, now)).toBeNull();
    expect(remaining('2027-02-01T12:00:00Z', now)).toBeNull();
    const r = remaining('2027-03-04T18:00:00-06:00', now)!;
    expect(formatRemaining(r)).toBe('3d 12:00:00');
    expect(formatRemaining({days: 0, hours: 2, minutes: 5, seconds: 9, totalMs: 0})).toBe('02:05:09');
  });
});
