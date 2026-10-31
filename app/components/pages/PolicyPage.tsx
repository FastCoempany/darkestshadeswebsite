import {Link} from 'react-router';
import {ReadingPage} from '~/components/pages/ReadingPage';
import {copy} from '~/lib/copy';

export type PolicyHandle = keyof typeof copy.policies.items;

export function isPolicyHandle(h: string): h is PolicyHandle {
  return Object.prototype.hasOwnProperty.call(copy.policies.items, h);
}

/**
 * The legal text comes from Shopify at launch. Until then: the title, the settled promises where they
 * apply (45-day exchange, 6-month warranty), and one draft line. Never drafted legal terms (RUN.md).
 */
export function PolicyPage({handle}: {handle: PolicyHandle}) {
  const line = handle === 'exchange' ? copy.policies.lines.exchange : handle === 'warranty' ? copy.policies.lines.warranty : null;
  return (
    <ReadingPage title={copy.policies.items[handle]}>
      {line ? <p>{line}</p> : null}
      <p className="text-ds-text-secondary">{copy.policies.pending}</p>
    </ReadingPage>
  );
}

export function PoliciesIndexPage() {
  return (
    <ReadingPage title={copy.policies.title}>
      <ul className="grid gap-1">
        {(Object.keys(copy.policies.items) as PolicyHandle[]).map((h) => (
          <li key={h}>
            <Link to={`/policies/${h}`} className="inline-flex min-h-11 items-center underline underline-offset-3">
              {copy.policies.items[h]}
            </Link>
          </li>
        ))}
      </ul>
    </ReadingPage>
  );
}
