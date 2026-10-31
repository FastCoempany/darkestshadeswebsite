import type {Route} from './+types/drops.$number';
import {DropPage} from '~/components/pages/DropPage';
import {dropSentence} from '~/components/house/DropStatus';
import {copy, fill, pageMeta} from '~/lib/copy';
import {dropView} from '~/lib/drop-view';

/** The drop's own sentence (state, date, numbers) is its description. A missing drop is titled by the root's meta. */
export const meta: Route.MetaFunction = ({data}) => pageMeta(data ? fill(copy.drop.heading, {number: data.drop.number}) : copy.nav.drop, data ? dropSentence(data.drop) : null);

/** The drop page carries its own status block and, while announced, its own sign-up: no drop line, no footer list. */
export const handle = {footerList: false, dropLine: false, listOffer: true};

export async function loader({params, context}: Route.LoaderArgs) {
  const drop = context.store.drops.byNumber(params.number);
  if (!drop) throw new Response('Not found', {status: 404});
  const view = dropView(drop, context)!;
  return {
    drop: view,
    products: context.store.products.all(),
    others: context.store.drops.all().filter((d) => d.number !== drop.number).map((d) => ({number: d.number, state: d.state})),
  };
}

export default function Drop({loaderData}: Route.ComponentProps) {
  return <DropPage {...loaderData} />;
}
