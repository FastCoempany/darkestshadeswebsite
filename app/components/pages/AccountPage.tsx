import {ReadingPage} from '~/components/pages/ReadingPage';
import {copy} from '~/lib/copy';

/** Shopify customer accounts are out of scope this phase; a placeholder (04). */
export function AccountPage() {
  return (
    <ReadingPage title={copy.account.title}>
      <p className="text-ds-text-secondary">{copy.account.pending}</p>
    </ReadingPage>
  );
}
