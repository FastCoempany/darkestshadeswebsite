import {Link} from 'react-router';
import {BrandMark} from '~/components/house/BrandMark';
import {Logo} from '~/components/house/Logo';
import {TextLink} from '~/components/base/TextLink';
import {copy, fill} from '~/lib/copy';
import {cx} from '~/lib/cx';

export interface HeaderProps {
  bagCount: number;
  onOpenMenu: () => void;
  onOpenBag: () => void;
  /** Transparent over the entry's end card and the manifesto; night surface after (04). */
  surface?: 'transparent' | 'solid';
  menuOpen?: boolean;
}

export const NAV = [
  {to: '/drop', label: copy.nav.drop},
  {to: '/frames', label: copy.nav.frames},
  {to: '/manifesto', label: copy.nav.manifesto},
] as const;

/**
 * 1024 px and up: the horizontal logo left, Drop · Frames · Manifesto in the middle, Bag (n) right, 64 px.
 * Under 1024: the brand mark left (never the GCD), Menu and Bag (n) right, 56 px.
 */
export function Header({bagCount, onOpenMenu, onOpenBag, surface = 'solid', menuOpen = false}: HeaderProps) {
  const bagLabel = bagCount > 0 ? (fill(copy.nav.bagWithCount, {count: bagCount}) ?? copy.nav.bag) : copy.nav.bag;
  const control = 'h-11 rounded-none px-2 font-text text-ui font-medium text-ds-text-primary hover:underline underline-offset-3';
  return (
    <header
      className={cx(
        'sticky top-0 z-(--z-header) grid h-(--layout-header-sm) grid-cols-[1fr_auto] items-center px-4 md:px-6 lg:h-(--layout-header-lg) lg:grid-cols-[1fr_auto_1fr] lg:px-10 xl:px-14',
        surface === 'solid' ? 'bg-ds-surface-canvas' : 'bg-transparent',
      )}
      data-surface={surface}
    >
      <Link to="/" className="inline-flex h-11 items-center text-ds-text-primary" aria-label={copy.meta.brand}>
        <span className="lg:hidden">
          <BrandMark height={22} />
        </span>
        <span className="hidden lg:block">
          <Logo variant="horizontal" height={16} />
        </span>
      </Link>
      <nav aria-label={copy.nav.primaryLabel} className="hidden items-center justify-center gap-8 lg:flex">
        {NAV.map((item) => (
          <TextLink key={item.to} to={item.to} variant="nav" className="text-ds-text-primary" activePrefix={item.to}>
            {item.label}
          </TextLink>
        ))}
      </nav>
      <div className="flex items-center justify-end gap-2">
        <button type="button" className={cx(control, 'lg:hidden')} onClick={onOpenMenu} aria-expanded={menuOpen} aria-haspopup="dialog">
          {copy.nav.menu}
        </button>
        <button type="button" className={control} onClick={onOpenBag} aria-haspopup="dialog">
          {bagLabel}
        </button>
      </div>
    </header>
  );
}
