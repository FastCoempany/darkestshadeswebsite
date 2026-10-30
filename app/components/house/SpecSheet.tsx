import {copy} from '~/lib/copy';
import {cx} from '~/lib/cx';
import type {StorefrontProduct} from '~/lib/mock/types';

/** The rows a frame's facts allow. A null value leaves its row out; nothing is ever invented (06-products.md). */
export function specRows(product: StorefrontProduct): {label: string; value: string}[] {
  const f = product.ds;
  const m = f.measurementsMm;
  const mm = (v: number | null) => (v === null ? null : `${v} mm`);
  const rows: [string, string | null][] = [
    [copy.product.specLabels.size, f.sizeNotation],
    [copy.product.specLabels.lensWidth, mm(m.lensWidth)],
    [copy.product.specLabels.bridge, mm(m.bridge)],
    [copy.product.specLabels.templeLength, mm(m.templeLength)],
    [copy.product.specLabels.lensHeight, mm(m.lensHeight)],
    [copy.product.specLabels.frontWidth, mm(m.frontWidth)],
    [copy.product.specLabels.front, f.frame.front],
    [copy.product.specLabels.temples, f.frame.temples],
    [copy.product.specLabels.lens, [f.lens.color, f.lens.type].filter(Boolean).join(' · ') || null],
    [copy.product.specLabels.protection, [f.lens.uv, f.lens.impact, f.lens.scratch].filter(Boolean).join(' · ') || null],
  ];
  return rows.filter((r): r is [string, string] => r[1] !== null && r[1] !== '').map(([label, value]) => ({label, value}));
}

export function SpecSheet({product, variant = 'full', className}: {product: StorefrontProduct; variant?: 'full' | 'compact'; className?: string}) {
  const rows = variant === 'compact' ? specRows(product).slice(0, 4) : specRows(product);
  if (!rows.length) return null;
  return (
    <div className={cx('grid', className)} data-spec-sheet>
      <dl className="grid">
        {rows.map((r) => (
          <div key={r.label} className="grid grid-cols-[minmax(7rem,1fr)_2fr] gap-4 border-t border-ds-border-hairline py-3">
            <dt className="font-text text-micro font-medium uppercase tracking-micro text-ds-text-tertiary">{r.label}</dt>
            <dd className="ds-tabular font-text text-body text-ds-text-primary">{r.value}</dd>
          </div>
        ))}
      </dl>
      {variant === 'full' ? <p className="pt-3 font-text text-small text-ds-text-tertiary">{copy.product.sizeHelp}</p> : null}
    </div>
  );
}
