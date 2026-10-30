/**
 * Storefront-API-shaped types for the mock adapter (docs/brief/09-build-plan.md, Data).
 *
 * Field names follow Shopify's Storefront API (Product, ProductVariant, Image, MoneyV2, Metaobject) so the
 * live client can replace app/lib/mock/index.ts at launch with no change to the routes. The `ds` members
 * carry Darkest Shades' own facts (from content/products/*.json) that Shopify will hold in `ds.*`
 * metafields and a `drop` metaobject (docs/brief/06-products.md, Shopify mapping).
 */

export interface MoneyV2 {
  amount: string;
  currencyCode: 'USD';
}

export type ImageFormat = 'avif' | 'webp' | 'jpg';

/** One final from assets/photography/MANIFEST.csv, as a Storefront `Image` plus its responsive set. */
export interface StorefrontImage {
  id: string;
  /** The JPEG at the largest width: the `src` fallback. */
  url: string;
  altText: string;
  width: number;
  height: number;
  ds: {
    /** Manifest id, e.g. `ds-f01-a2` or `ds-cast-w1-s07-f02`. */
    manifestId: string;
    /** Shot code for labels and wire mode, e.g. `F01-A2`, `F01-H`, `W1-S07-F02-A1`. */
    shot: string;
    frame: FrameId;
    angle: string;
    /** Aspect ratio as the design tokens name it: `stage` 4:5, `hero-landscape` 3:2. */
    ratio: 'stage' | 'hero-landscape' | 'print';
    ratioLabel: '4:5' | '3:2' | '3:4';
    widths: number[];
    formats: ImageFormat[];
    /** `srcset` strings per format, built from the manifest's widths. */
    srcset: Record<ImageFormat, string>;
    status: string;
    kind: 'product' | 'cast';
  };
}

export type FrameId = 'F01' | 'F02' | 'F03' | 'F04' | 'F05' | 'F06' | 'F08' | 'F09';

export interface Metafield {
  namespace: 'ds';
  key: string;
  type: string;
  value: string;
}

/** A frame's facts as content/products/f0X.json holds them. `null` means not set: the UI hides the row. */
export interface FrameFacts {
  id: FrameId;
  handle: string;
  lookNumber: string;
  name: string;
  descriptor: string;
  status: 'for-sale' | 'retired';
  frame: {shape: string | null; front: string | null; temples: string | null; fit: string | null};
  lens: {color: string | null; type: string | null; uv: string | null; impact: string | null; scratch: string | null};
  measurementsMm: {
    lensWidth: number | null;
    bridge: number | null;
    templeLength: number | null;
    lensHeight: number | null;
    frameHeight: number | null;
    frontWidth: number | null;
  };
  sizeNotation: string | null;
  gcd: {placement: string; lengthMm: number | null; stone?: string; metal?: string};
  copy: {line: string | null; story: string | null};
  promises: string[];
  lineArt: {front: string; side: string; top: string; iso: string};
}

export interface StorefrontVariant {
  id: string;
  title: string;
  sku: string;
  availableForSale: boolean;
  price: MoneyV2;
  compareAtPrice: null;
  /** Inventory. `null` = unknown, and the UI shows no count (honesty rules). */
  quantityAvailable: number | null;
  selectedOptions: {name: string; value: string}[];
  image: StorefrontImage | null;
  product: {handle: string; title: string};
}

export interface StorefrontProduct {
  id: string;
  handle: string;
  title: string;
  vendor: 'Darkest Shades';
  productType: 'Sunglasses';
  tags: string[];
  availableForSale: boolean;
  featuredImage: StorefrontImage | null;
  images: {nodes: StorefrontImage[]};
  priceRange: {minVariantPrice: MoneyV2; maxVariantPrice: MoneyV2};
  variants: {nodes: StorefrontVariant[]};
  selectedOrFirstAvailableVariant: StorefrontVariant;
  seo: {title: string | null; description: string | null};
  metafields: Metafield[];
  ds: FrameFacts;
}

export type DropState = 'announced' | 'live' | 'sold-out' | 'ended';

/** The drop as the UI reads it (content/drops/*.json; a `drop` metaobject in Shopify). */
export interface Drop {
  number: string;
  state: DropState;
  /** ISO 8601 with offset, or null when the founder has not set it. */
  startsAt: string | null;
  endsAt: string | null;
  timezone: string;
  frames: FrameId[];
  /** Pairs made per frame, or null: unknown. Never invented. */
  pairsPerFrame: number | null;
  limitPerCustomer: number | null;
  earlyAccess: {enabled: boolean; hoursBeforePublic: number | null};
  statement: string | null;
}

export interface StorefrontMetaobject {
  id: string;
  handle: string;
  type: 'drop';
  fields: {key: string; type: string; value: string | null}[];
}

export type CastId = 'W1' | 'W2' | 'W3' | 'M1' | 'M2' | 'M3' | 'NB';
export type SceneId = 'S01' | 'S02' | 'S03' | 'S04' | 'S05' | 'S06' | 'S07';

/** One planned on-model picture (content/photography/people/*.json). A draft is a labelled slot. */
export interface CastShot {
  /** Shot code: `W1-S07-F02-A1`. */
  code: string;
  cast: CastId;
  scene: SceneId;
  frame: FrameId;
  angle: 'A1' | 'A2';
  wardrobe: string;
  ratio: 'stage';
  ratioLabel: '4:5';
  status: 'final' | 'draft';
  /** The final's manifest id (`ds-cast-w1-s07-f02`) when it exists. */
  manifestId: string | null;
  image: StorefrontImage | null;
}

export interface CastMember {
  id: CastId;
  /** The studio portrait that stands for this person (RUN.md, Edge cases). */
  portrait: CastShot | null;
  shots: CastShot[];
}
