// The wall's types (DRAWER-WALL.md, "Every drawer is its own thing"). Records come in the shape of Shopify
// metaobjects; the adapter turns them into typed drawers; the resolver turns a drawer and its frame's facts into
// what the drawer does and says. Nothing here invents a fact: frame facts come from content/products/.

export type FrameId = 'F01' | 'F02' | 'F03' | 'F04' | 'F05' | 'F06' | 'F08' | 'F09';
export const FRAME_IDS: readonly FrameId[] = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F08', 'F09'];

/** A frame's facts, the subset of content/products/f0X.json the wall shows: its id, its handle (the deep link), its
 * look number, its name and its price. Nothing else ships; the asset checks read content/products/ themselves. A
 * value the record lacks is null, never filled in. */
export interface FrameFacts {
  id: FrameId;
  handle: string | null;
  lookNumber: string | null;
  name: string | null;
  price: { amount: string; currencyCode: string } | null;
}

/** A metaobject field as Shopify's Storefront API returns it (value is always a string or null; a list field's
 * value is a JSON array in that string). */
export interface MetaobjectField {
  key: string;
  type: string;
  value: string | null;
  reference?: unknown;
}

/** A metaobject: the shape both record kinds share. */
export interface Metaobject {
  id: string;
  handle: string;
  type: string;
  fields: MetaobjectField[];
}

export const BAY_STATES = ['available', 'sold_out', 'locked', 'hidden'] as const;
export type BayState = (typeof BAY_STATES)[number];
export const BAY_LIGHTS = ['auto', 'lit', 'dark'] as const;
export type BayLightSetting = (typeof BAY_LIGHTS)[number];
export const KNOB_STYLES = ['black-relief', 'gold', 'plain'] as const;
export type KnobStyle = (typeof KNOB_STYLES)[number];

/** A drawer's record as typed by the adapter: strings as they came, unknown values kept for the resolver to judge. */
export interface DrawerBayRecord {
  id: string;
  handle: string;
  frame: string | null;
  state: string | null;
  light: string | null;
  note: string | null;
}

/** The wall's record as typed by the adapter. */
export interface BayWallRecord {
  id: string;
  handle: string;
  bays: string[];
  knobStyle: string | null;
  renderSet: string | null;
}

export type SeamLight = 'lit' | 'dark';

/** What a drawer renders, from its record and its frame's facts (resolve.ts). A null label renders nothing. */
export interface BayLabel {
  lookNumber: string | null;
  name: string | null;
  price: string | null;
  soldOut: boolean;
  notYet: boolean;
}

export interface ResolvedBay {
  id: string;
  handle: string;
  state: BayState;
  light: SeamLight;
  frame: FrameFacts | null;
  canOpen: boolean;
  canLift: boolean;
  focusable: boolean;
  label: BayLabel | null;
  /** Why a drawer fell to hidden, for the log: never rendered. */
  problems: string[];
}

/** What the resolver asks of the assets: whether a frame's drawer can be seen and lifted. */
export interface AssetAvailability {
  hasSequence(frame: FrameId): boolean;
  hasLift(frame: FrameId): boolean;
}
