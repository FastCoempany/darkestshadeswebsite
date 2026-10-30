import {Link} from 'react-router';
import {Sheet} from '~/components/base/Sheet';
import {TextLink} from '~/components/base/TextLink';
import {DropLine} from '~/components/house/DropLine';
import type {DropView} from '~/lib/drop-view';
import {copy} from '~/lib/copy';

export interface MenuSheetProps {
  open: boolean;
  onClose: () => void;
  drop: DropView | null;
}

const DESTINATIONS = [
  {number: '01', to: '/drop', label: copy.nav.drop},
  {number: '02', to: '/frames', label: copy.nav.frames},
  {number: '03', to: '/manifesto', label: copy.nav.manifesto},
  {number: '04', to: '/cast', label: copy.nav.cast},
];

/** The phone menu: a full-screen night sheet, the four destinations in Owners Wide numbered 01–04 in camel, the drop line, the small links. Hard cut. */
export function MenuSheet({open, onClose, drop}: MenuSheetProps) {
  return (
    <Sheet open={open} onClose={onClose} variant="full" title={copy.nav.menu} hideTitle closeLabel={copy.nav.close}>
      <nav className="grid gap-10 py-8">
        <ol className="grid gap-6">
          {DESTINATIONS.map((d) => (
            <li key={d.to} className="grid grid-cols-[2.5rem_1fr] items-baseline gap-4">
              <span className="ds-tabular font-text text-micro font-medium uppercase tracking-micro text-ds-text-editorial">{d.number}</span>
              <Link to={d.to} onClick={onClose} className="ds-display text-display leading-display tracking-display text-ds-text-primary hover:underline underline-offset-4">
                {d.label}
              </Link>
            </li>
          ))}
        </ol>
        {drop ? <DropLine drop={drop} inline /> : null}
        <ul className="grid gap-3">
          <li>
            <TextLink to="/questions" variant="footer" onClick={onClose}>
              {copy.footer.links.questions}
            </TextLink>
          </li>
          <li>
            <TextLink to="/care" variant="footer" onClick={onClose}>
              {copy.footer.links.care}
            </TextLink>
          </li>
          <li>
            <TextLink to="https://instagram.com/darkestshades" variant="footer" external>
              {copy.meta.instagram}
            </TextLink>
          </li>
        </ul>
      </nav>
    </Sheet>
  );
}
