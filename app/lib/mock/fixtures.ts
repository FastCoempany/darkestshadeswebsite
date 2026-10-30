/**
 * Fixtures for states the real data does not have today: a drop with a date, a live drop with pair
 * counts, a sold-out and an ended drop. For stories and tests only. No route imports this file
 * (checks/layers.mjs enforces it): the site shows real data or nothing (CLAUDE.md, Honesty).
 */
import type {Drop, FrameId} from './types';

const FRAMES: FrameId[] = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F08', 'F09'];

export const dropAnnouncedNoDate: Drop = {
  number: '001',
  state: 'announced',
  startsAt: null,
  endsAt: null,
  timezone: 'America/Chicago',
  frames: FRAMES,
  pairsPerFrame: null,
  limitPerCustomer: null,
  earlyAccess: {enabled: false, hoursBeforePublic: 24},
  statement: null,
};

export const dropAnnouncedWithDate: Drop = {
  ...dropAnnouncedNoDate,
  startsAt: '2027-03-04T18:00:00-06:00',
  endsAt: '2027-03-11T18:00:00-06:00',
};

export const dropLive: Drop = {
  ...dropAnnouncedWithDate,
  state: 'live',
  startsAt: '2027-02-25T18:00:00-06:00',
  pairsPerFrame: 15,
  limitPerCustomer: 2,
};

export const dropSoldOut: Drop = {...dropLive, state: 'sold-out'};

export const dropEnded: Drop = {
  ...dropLive,
  state: 'ended',
  startsAt: '2026-11-05T18:00:00-06:00',
  endsAt: '2026-11-12T18:00:00-06:00',
};

/** Inventory a live drop might report: pairs left per frame. */
export const inventoryLive: Record<FrameId, number> = {
  F01: 7,
  F02: 0,
  F03: 15,
  F04: 3,
  F05: 12,
  F06: 1,
  F08: 9,
  F09: 15,
};

export const inventorySoldOut: Record<FrameId, number> = {
  F01: 0,
  F02: 0,
  F03: 0,
  F04: 0,
  F05: 0,
  F06: 0,
  F08: 0,
  F09: 0,
};
