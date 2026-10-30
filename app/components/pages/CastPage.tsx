import {CastFrame} from '~/components/house/CastFrame';
import {copy} from '~/lib/copy';
import type {CastMember, StorefrontProduct} from '~/lib/mock/types';

/** The seven, one per screen on a phone, full bleed, each linked to the frame they wear (04). */
export function CastPage({members, products}: {members: CastMember[]; products: StorefrontProduct[]}) {
  const byId = new Map(products.map((p) => [p.ds.id, p]));
  return (
    <main id="main" data-page="cast">
      <h1 className="sr-only">{copy.cast.title}</h1>
      <ul className="grid md:grid-cols-2 md:gap-6 md:px-6 md:py-12 lg:grid-cols-3 lg:px-10 xl:grid-cols-4 xl:px-14">
        {members.map((m, i) =>
          m.portrait ? (
            <li key={m.id}>
              <CastFrame shot={m.portrait} product={byId.get(m.portrait.frame) ?? null} variant="bleed" priority={i === 0} className="md:min-h-0" />
            </li>
          ) : null,
        )}
      </ul>
    </main>
  );
}
