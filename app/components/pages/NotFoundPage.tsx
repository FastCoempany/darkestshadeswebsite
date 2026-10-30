import {Link} from 'react-router';
import {BrandMark} from '~/components/house/BrandMark';
import {copy} from '~/lib/copy';

/** Any other path, and any failure: one line, the brand mark, a way back (04). */
export function NotFoundPage({status = 404}: {status?: number}) {
  const text = status === 404 ? copy.notFound : copy.error;
  return (
    <main id="main" className="grid min-h-dvh place-items-center px-4 py-16 text-center" data-page="not-found" data-status={status}>
      <div className="grid justify-items-center gap-8">
        <BrandMark height={40} />
        <h1 className="ds-display text-h1 leading-heading tracking-heading">{text.title}</h1>
        <Link className="inline-flex min-h-11 items-center font-text text-ui font-medium underline underline-offset-3" to="/">
          {text.link}
        </Link>
      </div>
    </main>
  );
}
