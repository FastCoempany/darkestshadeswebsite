// The eight frames' facts, from content/products/ at build time (virtual:wall-frames, vite.config.ts).
import frames from 'virtual:wall-frames';
import type { FrameFacts, FrameId } from '../lib/types';

export const FRAMES: Readonly<Partial<Record<FrameId, FrameFacts>>> = frames;

export function frameById(id: string | null | undefined): FrameFacts | null {
  return id && Object.prototype.hasOwnProperty.call(FRAMES, id) ? (FRAMES[id as FrameId] ?? null) : null;
}

export function frameByHandle(handle: string | null | undefined): FrameFacts | null {
  if (!handle) return null;
  return Object.values(FRAMES).find((f) => f?.handle === handle) ?? null;
}
