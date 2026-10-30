/**
 * Products from content/products/*.json, shaped like Storefront API `Product` objects.
 * Every fact comes from the files (the 1:1 drawings); nothing here invents a spec, a price or a quantity.
 */
import f01 from '../../../content/products/f01.json';
import f02 from '../../../content/products/f02.json';
import f03 from '../../../content/products/f03.json';
import f04 from '../../../content/products/f04.json';
import f05 from '../../../content/products/f05.json';
import f06 from '../../../content/products/f06.json';
import f08 from '../../../content/products/f08.json';
import f09 from '../../../content/products/f09.json';
import {castImagesFor, productImagesFor} from './manifest';
import type {Drop, FrameFacts, FrameId, Metafield, MoneyV2, StorefrontProduct, StorefrontVariant} from './types';

interface FrameFile {
  id: string;
  handle: string;
  lookNumber: string;
  name: string;
  descriptor: string;
  status: string;
  price: {amount: string; currencyCode: string};
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
  sources: {lineArt: string[]};
  copy: {line: string | null; story: string | null};
  promises: string[];
}

const files: FrameFile[] = [f01, f02, f03, f04, f05, f06, f08, f09];

function lineArt(paths: string[]): FrameFacts['lineArt'] {
  const find = (view: string) => paths.find((p) => p.endsWith(`-${view}.svg`)) ?? '';
  return {front: find('front'), side: find('side'), top: find('top'), iso: find('iso')};
}

export function facts(file: FrameFile): FrameFacts {
  return {
    id: file.id as FrameId,
    handle: file.handle,
    lookNumber: file.lookNumber,
    name: file.name,
    descriptor: file.descriptor,
    status: file.status === 'retired' ? 'retired' : 'for-sale',
    frame: file.frame,
    lens: file.lens,
    measurementsMm: file.measurementsMm,
    sizeNotation: file.sizeNotation,
    gcd: file.gcd,
    copy: file.copy,
    promises: file.promises,
    lineArt: lineArt(file.sources.lineArt),
  };
}

function money(file: FrameFile): MoneyV2 {
  if (file.price.currencyCode !== 'USD') throw new Error(`${file.id}: price must be in USD`);
  return {amount: file.price.amount, currencyCode: 'USD'};
}

function metafields(f: FrameFacts): Metafield[] {
  const m = (key: string, type: string, value: string | number | null): Metafield | null =>
    value === null || value === undefined ? null : {namespace: 'ds', key, type, value: String(value)};
  return [
    m('look_number', 'single_line_text_field', f.lookNumber),
    m('descriptor', 'single_line_text_field', f.descriptor),
    m('size_notation', 'single_line_text_field', f.sizeNotation),
    m('measurements', 'json', JSON.stringify(f.measurementsMm)),
    m('lens_color', 'single_line_text_field', f.lens.color),
    m('gcd_length_mm', 'number_decimal', f.gcd.lengthMm),
    m('line_art', 'json', JSON.stringify(f.lineArt)),
  ].filter((x): x is Metafield => x !== null);
}

/** Build the product list for a drop state. Availability follows the drop; inventory stays unknown (null). */
export function buildProducts(drop: Drop | null): StorefrontProduct[] {
  return files
    .map((file) => {
      const f = facts(file);
      const inDrop = drop?.frames.includes(f.id) ?? false;
      const available = inDrop && drop?.state === 'live';
      const price = money(file);
      const images = [...productImagesFor(f.id), ...castImagesFor(f.id)];
      const variant: StorefrontVariant = {
        id: `gid://shopify/ProductVariant/${f.id}-01`,
        title: 'Default Title',
        sku: `DS-${f.id}-01`,
        availableForSale: available,
        price,
        compareAtPrice: null,
        quantityAvailable: null,
        selectedOptions: [{name: 'Title', value: 'Default Title'}],
        image: images[0] ?? null,
        product: {handle: f.handle, title: f.name},
      };
      const tags = [`look-${f.lookNumber}`];
      if (drop && inDrop) tags.push(`drop-${drop.number}`);
      return {
        id: `gid://shopify/Product/${f.id}`,
        handle: f.handle,
        title: f.name,
        vendor: 'Darkest Shades' as const,
        productType: 'Sunglasses' as const,
        tags,
        availableForSale: available,
        featuredImage: images[0] ?? null,
        images: {nodes: images},
        priceRange: {minVariantPrice: price, maxVariantPrice: price},
        variants: {nodes: [variant]},
        selectedOrFirstAvailableVariant: variant,
        seo: {title: f.name, description: null},
        metafields: metafields(f),
        ds: f,
      };
    })
    .filter((p) => p.ds.status === 'for-sale')
    .sort((a, b) => a.ds.lookNumber.localeCompare(b.ds.lookNumber));
}
