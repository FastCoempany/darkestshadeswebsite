import horizontal from '../../../brand/marks/web/ds-logo-horizontal.svg?raw';
import stacked from '../../../brand/marks/web/ds-logo-stacked.svg?raw';
import {cx} from '~/lib/cx';

/**
 * Anastasiia's primary logo: the angular brand mark with DARKEST SHADES on one line (`horizontal`:
 * the desktop header, the footer) or stacked (`stacked`: square-ish spaces, the entry's end card).
 * Inline SVG from brand/marks/web, in the current text color; never recolored to gold, never stretched
 * (docs/brief/01-brand-system.md). The SVG carries its own title for screen readers.
 */
export function Logo({
  variant = 'horizontal',
  height = 20,
  className,
}: {
  variant?: 'horizontal' | 'stacked';
  /** Rendered height in CSS pixels; the width follows the mark's own proportion. */
  height?: number;
  className?: string;
}) {
  return (
    <span
      className={cx('ds-mark inline-block', className)}
      style={{height}}
      dangerouslySetInnerHTML={{__html: variant === 'stacked' ? stacked : horizontal}}
    />
  );
}
