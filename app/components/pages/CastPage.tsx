import {CastFrame} from '~/components/house/CastFrame';
import {copy} from '~/lib/copy';
import {cx} from '~/lib/cx';
import type {CastMember, StorefrontProduct} from '~/lib/mock/types';

/** The seven, one per screen on a phone, full bleed, each linked to the frame they wear (04). */
export function CastPage({members, products}: {members: CastMember[]; products: StorefrontProduct[]}) {
  const byId = new Map(products.map((p) => [p.ds.id, p]));
  return (
    <main id="main" data-page="cast">
      <h1 className="sr-only">{copy.cast.title}</h1>
      {/* Seven portraits: two, three, then four across, the last row centred so no cell stays empty. */}
      <ul className="grid md:grid-cols-4 md:gap-6 md:px-6 md:py-12 lg:grid-cols-6 lg:px-10 xl:grid-cols-8 xl:px-14">
        {members.map((m, i) =>
          m.portrait ? (
            <li key={m.id} className={cx('md:col-span-2', i === 4 && 'xl:col-start-2', i === 6 && 'md:col-start-2 lg:col-start-3 xl:col-start-auto')}>
              <CastFrame shot={m.portrait} product={byId.get(m.portrait.frame) ?? null} variant="bleed" priority={i === 0} sizes="(min-width: 1440px) 25vw, (min-width: 1024px) 33vw, (min-width: 768px) 50vw, 100vw" className="md:min-h-0" />
            </li>
          ) : null,
        )}
      </ul>
      <p className="px-4 pb-12 pt-6 font-text text-small text-ds-text-tertiary md:px-6 md:pt-0 lg:px-10 xl:px-14">{copy.product.imageDisclosure}</p>
    </main>
  );
}
