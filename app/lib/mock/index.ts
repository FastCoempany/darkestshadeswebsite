/**
 * The mock store: local data in Storefront API shape (docs/brief/09-build-plan.md, Data).
 * This is the one module to replace with the live Storefront client at launch. Routes reach it as
 * `context.store`. It makes no network calls.
 */
import {members, shots, shotsForFrame} from './cast';
import {currentDrop, drops, effectiveState} from './drops';
import {castImagesFor, imageById, imageForShot, images, productImagesFor} from './manifest';
import {buildProducts} from './products';
import type {CastId, Drop, FrameId, StorefrontProduct} from './types';

export type * from './types';
export {effectiveState} from './drops';

export function createStore(now: Date = new Date()) {
  const current = currentDrop(drops, now);
  const products = buildProducts(current);
  return {
    products: {
      all: (): StorefrontProduct[] => products,
      byHandle: (handle: string): StorefrontProduct | null => products.find((p) => p.handle === handle) ?? null,
      byId: (id: FrameId): StorefrontProduct | null => products.find((p) => p.ds.id === id) ?? null,
      byLook: (look: string): StorefrontProduct | null => products.find((p) => p.ds.lookNumber === look) ?? null,
      /** The frame after this one by look number, wrapping to the first. */
      next: (id: FrameId): StorefrontProduct | null => {
        const i = products.findIndex((p) => p.ds.id === id);
        return i < 0 ? null : (products[(i + 1) % products.length] ?? null);
      },
    },
    drops: {
      all: (): Drop[] => drops.map((d) => ({...d, state: effectiveState(d, now)})),
      current: (): Drop | null => current,
      byNumber: (number: string): Drop | null => {
        const d = drops.find((x) => x.number === number);
        return d ? {...d, state: effectiveState(d, now)} : null;
      },
    },
    images: {
      all: () => images,
      byId: imageById,
      forFrame: productImagesFor,
      castForFrame: castImagesFor,
      forShot: imageForShot,
    },
    cast: {
      members: () => members,
      member: (id: CastId) => members.find((m) => m.id === id) ?? null,
      shots: () => shots,
      shotsForFrame,
    },
  };
}

export type Store = ReturnType<typeof createStore>;

/** The default store, built once per server start. */
export const store: Store = createStore();
