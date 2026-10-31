import {Link} from 'react-router';
import {Button} from '~/components/base/Button';
import {DropStatus, type DropView} from '~/components/house/DropStatus';
import {ListForm} from '~/components/house/ListForm';
import {StageCard} from '~/components/house/StageCard';
import {copy, fill} from '~/lib/copy';
import {lineFor, useCart} from '~/lib/cart';
import type {StorefrontProduct} from '~/lib/mock/types';

export interface DropPageProps {
  drop: DropView;
  products: StorefrontProduct[];
  /** Other drops, for the archive list. */
  others?: {number: string; state: string}[];
}

/** "Drop 001" and one statement, the status block, the frames as stage cards; past drops stay up (04). */
export function DropPage({drop, products, others = []}: DropPageProps) {
  const {add} = useCart();
  const inDrop = products.filter((p) => drop.frames.includes(p.ds.id));
  return (
    <main id="main" className="grid gap-16 px-4 py-12 md:px-6 lg:px-10 xl:px-14" data-page="drop" data-drop-state={drop.state}>
      <header className="grid gap-6">
        <h1 className="ds-display text-display leading-display tracking-display">{fill(copy.drop.heading, {number: drop.number})}</h1>
        {drop.statement ? <p className="ds-measure font-text text-body-lg font-book text-ds-text-secondary">{drop.statement}</p> : null}
      </header>

      <section aria-label={copy.drop.stateWords[drop.state === 'sold-out' ? 'soldOut' : drop.state]} className={drop.state === 'announced' ? 'grid gap-12 lg:grid-cols-2 lg:gap-8' : 'grid gap-8'}>
        <DropStatus drop={drop} variant="block" />
        {drop.state === 'announced' ? (
          <div className="grid gap-4">
            <h2 className="ds-display text-label leading-ui tracking-label text-ds-text-secondary">{copy.product.notify}</h2>
            <ListForm scope="drop" />
          </div>
        ) : null}
      </section>

      <section aria-label={copy.nav.frames}>
        <ul className="grid grid-cols-1 gap-x-4 gap-y-10 md:grid-cols-2 lg:grid-cols-4">
          {inDrop.map((p, i) => {
            const left = drop.inventory?.[p.ds.id];
            const soldOut = drop.state === 'sold-out' || (drop.state === 'live' && left === 0);
            return (
              <li key={p.id} className="grid gap-4">
                <StageCard product={p} drop={drop} priority={i < 2} heading="h2" />
                {drop.state === 'live' || drop.state === 'sold-out' ? (
                  <Button variant="outline" size={48} disabled={soldOut} onClick={() => add(lineFor(p, p.variants.nodes[0]), drop.limitPerCustomer)}>
                    {soldOut ? copy.product.soldOut : copy.product.addToBag}
                  </Button>
                ) : null}
              </li>
            );
          })}
        </ul>
      </section>

      {others.length ? (
        <section aria-labelledby="drop-archive" className="grid gap-4">
          <h2 id="drop-archive" className="ds-display text-label leading-ui tracking-label text-ds-text-secondary">
            {copy.drop.archive}
          </h2>
          <ul className="grid gap-2">
            {others.map((o) => (
              <li key={o.number}>
                <Link to={`/drops/${o.number}`} className="inline-flex min-h-11 items-center font-text text-body underline underline-offset-3">
                  {fill(copy.drop.heading, {number: o.number})}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}
