import type {ReactNode} from 'react';
import {toDropView, type DropView} from '~/lib/drop-view';
import {PageShell} from '~/components/house/PageShell';
import {CartProvider, emptyCart, lineFor, type Cart} from '~/lib/cart';
import {store} from '~/lib/mock';
import {dropAnnouncedNoDate, dropAnnouncedWithDate, dropEnded, dropLive, dropSoldOut, inventoryLive, inventorySoldOut} from '~/lib/mock/fixtures';

/** A fixed clock for stories, so countdowns and dates render the same every time. */
export const STORY_NOW = new Date('2027-03-01T18:00:00Z');

export const products = store.products.all();
export const cast = store.cast.members();

export const drops: Record<'announcedNoDate' | 'announcedWithDate' | 'live' | 'soldOut' | 'ended', DropView> = {
  announcedNoDate: toDropView(dropAnnouncedNoDate, STORY_NOW, null, null)!,
  announcedWithDate: toDropView(dropAnnouncedWithDate, STORY_NOW, null, null)!,
  live: toDropView(dropLive, STORY_NOW, inventoryLive, null)!,
  soldOut: toDropView(dropSoldOut, STORY_NOW, inventorySoldOut, null)!,
  ended: toDropView(dropEnded, STORY_NOW, inventorySoldOut, null)!,
};

const f01 = products[0];
const f09 = products[products.length - 1];
export const fullBag: Cart = {
  ...emptyCart,
  lines: {nodes: [lineFor(f01, f01.variants.nodes[0], 1), lineFor(f09, f09.variants.nodes[0], 2)]},
};

/** The page inside the shell, with a bag and a drop state. */
export function Page({children, drop = drops.announcedNoDate, bag = emptyCart, bagOpen = false, headerSurface, footerList = true, dropLine = true}: {children: ReactNode; drop?: DropView | null; bag?: Cart; bagOpen?: boolean; headerSurface?: 'transparent' | 'solid'; footerList?: boolean; dropLine?: boolean}) {
  return (
    <CartProvider persist={false} initialCart={bag} initialOpen={bagOpen}>
      <PageShell drop={drop} year={STORY_NOW.getFullYear()} headerSurface={headerSurface} showFooterList={footerList} showDropLine={dropLine}>
        {children}
      </PageShell>
    </CartProvider>
  );
}
