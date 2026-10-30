import {useState, type ReactNode} from 'react';
import {SkipLink} from '~/components/base/SkipLink';
import {BagDrawer} from '~/components/house/BagDrawer';
import {DropLine} from '~/components/house/DropLine';
import type {DropView} from '~/lib/drop-view';
import {Footer} from '~/components/house/Footer';
import {Header} from '~/components/house/Header';
import {MenuSheet} from '~/components/house/MenuSheet';
import {useCart} from '~/lib/cart';
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
}

/** Skip link, header, the drop line, the page, the footer, and the menu and bag sheets. Inside a CartProvider. */
export function PageShell({drop, year, children, headerSurface = 'solid', showFooter = true, showFooterList = true, showDropLine = true}: PageShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const {cart, open: openBag} = useCart();
  return (
    <>
      <SkipLink>{copy.nav.skipToContent}</SkipLink>
      <Header bagCount={cart.totalQuantity} onOpenMenu={() => setMenuOpen(true)} onOpenBag={openBag} surface={headerSurface} menuOpen={menuOpen} />
      {showDropLine ? <DropLine drop={drop} /> : null}
      {children}
      {showFooter ? <Footer year={year} showList={showFooterList} /> : null}
      <MenuSheet open={menuOpen} onClose={() => setMenuOpen(false)} drop={drop} />
      <BagDrawer limit={drop?.limitPerCustomer ?? null} />
    </>
  );
}
