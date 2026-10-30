import type {Route} from './+types/drops.$number';
import {DropPage} from '~/components/pages/DropPage';
import {copy, fill, pageTitle} from '~/lib/copy';
import {dropView} from '~/lib/drop-view';

export const meta: Route.MetaFunction = ({data}) => [{title: pageTitle(data ? fill(copy.drop.heading, {number: data.drop.number}) : copy.nav.drop)}];

/** The drop page carries its own status block and, while announced, its own sign-up: no drop line, no footer list. */
export const handle = {footerList: false, dropLine: false};

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
