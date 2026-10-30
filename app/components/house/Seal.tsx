import flatGold from '../../../brand/emblems/gcd/svg/gcd-flat-gold.svg?url';
import goldBlack from '../../../brand/emblems/gcd/svg/gcd-gold-black.svg?url';
import onyx from '../../../brand/emblems/gcd/svg/gcd-onyx.svg?url';
import render1024 from '../../../brand/emblems/gcd/render/gcd-3d-front-1024.png?url';
import render4096 from '../../../brand/emblems/gcd/render/gcd-3d-front-4096.png?url';
import {copy} from '~/lib/copy';
import {cx} from '~/lib/cx';

/** The GCD master is 1632 x 589 units; the 3D renders are 1024 x 414 and 4096 x 1656. */
const RATIO = 589 / 1632;

/**
 * The God Cloud Device as a seal (docs/brief/01-brand-system.md, GCD rules). Size steps by rendered
 * width: under 48 px the flat gold vector (no veins); 48 to 160 px the onyx vector (metallic gradient,
 * veins); above 160 px the 3D render. On paper surfaces the flat version is gold with a black stone,
 * because flat gold on paper is decoration only. At most one Seal per screen; never in the nav.
 */
export function Seal({
  width = 96,
  surface = 'night',
  decorative = false,
  className,
}: {
  /** Rendered width in CSS pixels. */
  width?: number;
  surface?: 'night' | 'paper';
  /** True when the seal repeats something already said in text next to it. */
  decorative?: boolean;
  className?: string;
}) {
  const height = Math.round(width * RATIO);
  let src: string;
  let srcSet: string | undefined;
  if (width > 160) {
    src = render1024;
    srcSet = `${render1024} 1024w, ${render4096} 4096w`;
  } else if (width >= 48) {
    src = surface === 'paper' ? goldBlack : onyx;
  } else {
    src = surface === 'paper' ? goldBlack : flatGold;
  }
  return (
    <span className={cx('ds-seal relative inline-block', className)} data-shot="GCD seal" style={{width, height}}>
      <img
        className="block"
        src={src}
        srcSet={srcSet}
        sizes={srcSet ? `${width}px` : undefined}
        width={width}
        height={height}
        alt={decorative ? '' : copy.alt.seal}
        aria-hidden={decorative || undefined}
        decoding="async"
      />
    </span>
  );
}
