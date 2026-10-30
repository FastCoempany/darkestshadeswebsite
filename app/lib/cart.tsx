/**
 * The bag in this phase: local state in the Storefront cart API's shape, kept in localStorage, no
 * Shopify calls and no checkout (docs/build/RUN.md, phase 0). At launch Hydrogen's cart handler takes
 * over and the components keep reading the same shape.
 */
import {createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode} from 'react';
import type {MoneyV2, StorefrontImage, StorefrontProduct, StorefrontVariant} from '~/lib/mock/types';

export interface CartLine {
  id: string;
  quantity: number;
  merchandise: {
    id: string;
    title: string;
    sku: string;
    price: MoneyV2;
    image: StorefrontImage | null;
    product: {handle: string; title: string; lookNumber: string; descriptor: string};
  };
  cost: {totalAmount: MoneyV2};
}

export interface Cart {
  id: string;
  totalQuantity: number;
  lines: {nodes: CartLine[]};
  cost: {subtotalAmount: MoneyV2; totalAmount: MoneyV2};
  /** No checkout in this phase. */
  checkoutUrl: null;
}

const STORAGE_KEY = 'ds_bag';

function money(amount: number): MoneyV2 {
  return {amount: amount.toFixed(2), currencyCode: 'USD'};
}

function withTotals(lines: CartLine[]): Cart {
  const subtotal = lines.reduce((sum, l) => sum + Number(l.merchandise.price.amount) * l.quantity, 0);
  return {
    id: 'gid://shopify/Cart/local',
    totalQuantity: lines.reduce((n, l) => n + l.quantity, 0),
    lines: {nodes: lines.map((l) => ({...l, cost: {totalAmount: money(Number(l.merchandise.price.amount) * l.quantity)}}))},
    cost: {subtotalAmount: money(subtotal), totalAmount: money(subtotal)},
    checkoutUrl: null,
  };
}

export const emptyCart: Cart = withTotals([]);

export function lineFor(product: StorefrontProduct, variant: StorefrontVariant, quantity = 1): CartLine {
  return {
    id: `gid://shopify/CartLine/${variant.id.split('/').pop()}`,
    quantity,
    merchandise: {
      id: variant.id,
      title: variant.title,
      sku: variant.sku,
      price: variant.price,
      image: product.featuredImage,
      product: {handle: product.handle, title: product.title, lookNumber: product.ds.lookNumber, descriptor: product.ds.descriptor},
    },
    cost: {totalAmount: money(Number(variant.price.amount) * quantity)},
  };
}

export interface CartApi {
  cart: Cart;
  /** True after the stored bag has been read on the client (SSR renders the empty bag). */
  ready: boolean;
  isOpen: boolean;
  open: () => void;
  close: () => void;
  add: (line: CartLine, limit?: number | null) => void;
  setQuantity: (lineId: string, quantity: number, limit?: number | null) => void;
  remove: (lineId: string) => void;
}

const CartContext = createContext<CartApi | null>(null);

function clamp(quantity: number, limit: number | null | undefined): number {
  const max = limit && limit > 0 ? limit : Infinity;
  return Math.max(0, Math.min(quantity, max));
}

export function CartProvider({children, initialCart = emptyCart, initialOpen = false, persist = true}: {children: ReactNode; initialCart?: Cart; initialOpen?: boolean; persist?: boolean}) {
  const [lines, setLines] = useState<CartLine[]>(initialCart.lines.nodes);
  const [ready, setReady] = useState(!persist);
  const [isOpen, setOpen] = useState(initialOpen);

  useEffect(() => {
    if (!persist) return;
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) setLines((JSON.parse(stored) as Cart).lines.nodes);
    } catch {
      // A bag that cannot be read starts empty.
    }
    setReady(true);
  }, [persist]);

  useEffect(() => {
    if (!persist || !ready) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(withTotals(lines)));
    } catch {
      // Storage may be unavailable; the bag still works for the visit.
    }
  }, [lines, persist, ready]);

  const add = useCallback((line: CartLine, limit?: number | null) => {
    setLines((prev) => {
      const existing = prev.find((l) => l.merchandise.id === line.merchandise.id);
      if (existing) {
        return prev.map((l) => (l === existing ? {...l, quantity: clamp(l.quantity + line.quantity, limit)} : l));
      }
      return [...prev, {...line, quantity: clamp(line.quantity, limit)}];
    });
    setOpen(true);
  }, []);
  const setQuantity = useCallback((lineId: string, quantity: number, limit?: number | null) => {
    setLines((prev) => prev.map((l) => (l.id === lineId ? {...l, quantity: clamp(quantity, limit)} : l)).filter((l) => l.quantity > 0));
  }, []);
  const remove = useCallback((lineId: string) => setLines((prev) => prev.filter((l) => l.id !== lineId)), []);
  const open = useCallback(() => setOpen(true), []);
  const close = useCallback(() => setOpen(false), []);

  const value = useMemo<CartApi>(() => ({cart: withTotals(lines), ready, isOpen, open, close, add, setQuantity, remove}), [lines, ready, isOpen, open, close, add, setQuantity, remove]);
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartApi {
  const api = useContext(CartContext);
  if (!api) throw new Error('useCart needs a CartProvider');
  return api;
}
