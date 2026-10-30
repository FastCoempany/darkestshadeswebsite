import type {DropView} from '~/components/house/DropStatus';
import {StageCard} from '~/components/house/StageCard';
import {copy} from '~/lib/copy';
import type {StorefrontProduct} from '~/lib/mock/types';

/**
 * One statement line, then the eight as numbered stage cards: 1 across at 390, 2 at 768, 4 from 1024.
 * (Three across would put F04 and F05 side by side, which 06-products.md forbids; see PROGRESS.md.)
 */
export function FramesPage({products, drop}: {products: StorefrontProduct[]; drop: DropView | null}) {
  return (
    <main id="main" className="grid gap-12 px-4 py-12 md:px-6 lg:px-10 xl:px-14" data-page="frames">
      <header className="grid gap-4">
        <h1 className="sr-only">{copy.frames.title}</h1>
        <p className="ds-display text-display leading-display tracking-display">{copy.frames.statement}</p>
      </header>
      <ul className="grid grid-cols-1 gap-x-4 gap-y-12 md:grid-cols-2 lg:grid-cols-4">
        {products.map((p, i) => (
          <li key={p.id}>
            <StageCard product={p} drop={drop} priority={i < 2} heading="h2" />
          </li>
        ))}
      </ul>
    </main>
  );
}
