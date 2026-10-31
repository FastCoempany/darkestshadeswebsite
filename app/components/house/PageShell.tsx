import {useEffect, useState, type ReactNode} from 'react';
import {SkipLink} from '~/components/base/SkipLink';
import {BagDrawer} from '~/components/house/BagDrawer';
import {DropLine} from '~/components/house/DropLine';
import type {DropView} from '~/lib/drop-view';
import {Footer} from '~/components/house/Footer';
import {Header} from '~/components/house/Header';
import {ListOffer} from '~/components/house/ListOffer';
import {MenuSheet} from '~/components/house/MenuSheet';
import {useCart} from '~/lib/cart';
import {useListOffer} from '~/lib/list-offer';
import {copy} from '~/lib/copy';

export interface PageShellProps {
  drop: DropView | null;
  /** The year for the copyright line, from the request clock. */
  year: number;
  children: ReactNode;
  /** The header is transparent over the entry's end card and the manifesto. */
  headerSurface?: 'transparent' | 'solid';
  showFooter?: boolean;
  showFooterList?: boolean;
  /** The drop page shows its own status block instead of the line. */
  showDropLine?: boolean;
  /** Home, drop and frame pages open the list pop-up once, at 60% scroll (04, Overlays). */
  listOffer?: boolean;
}

/** Skip link, header, the drop line, the page, the footer, and the menu and bag sheets. Inside a CartProvider. */
export function PageShell({drop, year, children, headerSurface = 'solid', showFooter = true, showFooterList = true, showDropLine = true, listOffer = false}: PageShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const {cart, open: openBag} = useCart();
  const offer = useListOffer(listOffer);

  // A transparent header (over the entry's end card and the manifesto) turns to the night surface after the first screen.
  useEffect(() => {
    if (headerSurface !== 'transparent') return;
    const onScroll = () => {
      const manifesto = document.querySelector('[data-manifesto]');
      const past = manifesto ? manifesto.getBoundingClientRect().bottom <= 0 : window.scrollY > window.innerHeight * 0.6;
      setScrolled(past);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, {passive: true});
    return () => window.removeEventListener('scroll', onScroll);
  }, [headerSurface]);
  const surface = headerSurface === 'transparent' && !scrolled ? 'transparent' : 'solid';
  return (
    <>
      <SkipLink>{copy.nav.skipToContent}</SkipLink>
      <Header bagCount={cart.totalQuantity} onOpenMenu={() => setMenuOpen(true)} onOpenBag={openBag} surface={surface} menuOpen={menuOpen} />
      {showDropLine ? <DropLine drop={drop} /> : null}
      {children}
      {showFooter ? <Footer year={year} showList={showFooterList} /> : null}
      <MenuSheet open={menuOpen} onClose={() => setMenuOpen(false)} drop={drop} />
      <BagDrawer limit={drop?.limitPerCustomer ?? null} />
      {listOffer ? <ListOffer open={offer.open} onClose={offer.close} onSignedUp={offer.joined} earlyAccess={drop ? {enabled: drop.earlyAccess.enabled, hours: drop.earlyAccess.hoursBeforePublic} : undefined} /> : null}
    </>
  );
}
