import {copy, fill} from '~/lib/copy';
import {cx} from '~/lib/cx';
import type {Drawings, DrawingView as View} from '~/lib/drawings';
import type {StorefrontProduct} from '~/lib/mock/types';

/** Strips the file's own width and height so the drawing scales to its box, keeping the viewBox (1:1 mm). */
function inline(svg: string): string {
  return svg.replace(/\swidth="[^"]*"/, '').replace(/\sheight="[^"]*"/, '').replace('<svg ', '<svg role="img" aria-hidden="true" focusable="false" ');
}

export interface LineDrawingProps {
  product: StorefrontProduct;
  /** The frame's drawings as SVG text, read on the server for this frame only (app/lib/drawings.ts). */
  drawings: Drawings;
  views?: View[];
  variant?: 'single' | 'triptych' | 'print';
  className?: string;
}

/**
 * The frame's technical drawing as inline SVG (content/products/drawings, tools/drawings.py), strokes in the
 * text color, with the key measurements from the product file (06-products.md).
 */
export function LineDrawing({product, drawings, views = ['front', 'side', 'top'], variant = 'triptych', className}: LineDrawingProps) {
  const subject = copy.alt.subjects[product.ds.id];
  const m = product.ds.measurementsMm;
  const measures = [
    m.frontWidth !== null ? `${copy.product.specLabels.frontWidth} ${m.frontWidth} mm` : null,
    m.lensHeight !== null ? `${copy.product.specLabels.lensHeight} ${m.lensHeight} mm` : null,
    m.templeLength !== null ? `${copy.product.specLabels.templeLength} ${m.templeLength} mm` : null,
  ].filter(Boolean);
  return (
    <div className={cx('grid items-end gap-8', variant === 'triptych' && 'lg:grid-cols-3', className)} data-line-drawing={product.ds.id}>
      {views.map((view) => {
        const svg = drawings[view] ?? null;
        if (!svg) return null;
        const label = fill(copy.alt.lineDrawing, {subject, view: copy.alt.views[view]});
        return (
          <figure key={view} className="grid content-start gap-3">
            <div className="text-ds-text-primary [&>svg]:h-auto [&>svg]:w-full" role="img" aria-label={label ?? undefined} dangerouslySetInnerHTML={{__html: inline(svg)}} />
            <figcaption className="font-text text-micro font-medium uppercase tracking-micro text-ds-text-tertiary">
              {copy.product.drawnViews[view as 'front' | 'side' | 'top'] ?? copy.alt.views[view]}
            </figcaption>
          </figure>
        );
      })}
      {measures.length ? <p className="ds-tabular font-text text-small text-ds-text-secondary lg:col-span-3">{measures.join(' · ')}</p> : null}
    </div>
  );
}
