import {Button} from '~/components/base/Button';
import {Sheet} from '~/components/base/Sheet';
import {ListForm} from '~/components/house/ListForm';
import {copy} from '~/lib/copy';

export interface ListOfferProps {
  open: boolean;
  onClose: () => void;
  onSignedUp?: () => void;
  /** Only when the store really gates the drop for list members (00-decisions.md O6). */
  earlyAccess?: {enabled: boolean; hours: number | null};
}

/** The 60% scroll pop-up: information and access, never money. Closes with Esc, the button, or a click outside. */
export function ListOffer({open, onClose, onSignedUp, earlyAccess}: ListOfferProps) {
  const body = earlyAccess?.enabled && earlyAccess.hours ? copy.list.body.replace('{hours}', String(earlyAccess.hours)) : copy.list.bodyNoEarlyAccess;
  return (
    <Sheet open={open} onClose={onClose} variant="center" title={copy.list.title} closeLabel={copy.nav.close} className="z-(--z-offer)">
      <div className="grid gap-6 py-2">
        <p className="font-text text-body text-ds-text-secondary">{body}</p>
        <ListForm scope="offer" onSuccess={onSignedUp} />
        <Button variant="quiet" onClick={onClose}>
          {copy.list.dismiss}
        </Button>
      </div>
    </Sheet>
  );
}
