import mark from '../../../brand/marks/web/ds-brand-mark.svg?raw';
import {cx} from '~/lib/cx';

/**
 * The angular brand mark alone: the nav on small screens, the favicon, the 404, loading states.
 * Never the GCD here (docs/brief/00-decisions.md #11). Inline SVG in the current text color.
 */
export function BrandMark({height = 24, className}: {height?: number; className?: string}) {
  return (
    <span className={cx('ds-mark inline-block', className)} style={{height}} dangerouslySetInnerHTML={{__html: mark}} />
  );
}
