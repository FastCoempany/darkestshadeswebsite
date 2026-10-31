import type {DsLoadContext} from '~/lib/context';
import type {Drop, FrameId} from '~/lib/mock/types';

/** The drop as pages receive it: the data plus the request clock and inventory, all serializable. */
export interface DropView extends Drop {
  /** ISO at render. */
  now: string;
  /** Pairs left per frame from inventory, or null: unknown. */
  inventory: Record<FrameId, number> | null;
  /** Sum of the inventory, or null. */
  pairsLeft: number | null;
  /** pairsPerFrame × frames, or null. */
  pairsTotal: number | null;
  /** The founder's threshold, or null. */
  threshold: number | null;
}

export function toDropView(drop: Drop | null, now: Date, inventory: Record<FrameId, number> | null, threshold: number | null): DropView | null {
  if (!drop) return null;
  // A count only when every frame in the drop has a number; a partial record is no total (honesty).
  const complete = inventory !== null && drop.frames.every((f) => Number.isFinite(inventory[f]));
  const pairsLeft = complete ? drop.frames.reduce((sum, f) => sum + inventory![f], 0) : null;
  const pairsTotal = drop.pairsPerFrame !== null ? drop.pairsPerFrame * drop.frames.length : null;
  return {...drop, now: now.toISOString(), inventory, pairsLeft, pairsTotal, threshold};
}

/** The current drop as pages receive it. Inventory is unknown in this phase (null), so no count renders. */
export function currentDropView(context: DsLoadContext): DropView | null {
  return toDropView(context.store.drops.current(), context.now, null, context.settings.pairsLeftThreshold);
}

export function dropView(drop: Drop | null, context: DsLoadContext): DropView | null {
  return toDropView(drop, context.now, null, context.settings.pairsLeftThreshold);
}
