import type {Route} from './+types/cart';
import {BagPage} from '~/components/pages/BagPage';
import {copy, pageTitle} from '~/lib/copy';

export const meta: Route.MetaFunction = () => [{title: pageTitle(copy.bag.title)}];

export async function loader({context}: Route.LoaderArgs) {
  return {limit: context.store.drops.current()?.limitPerCustomer ?? null};
}

export default function Cart({loaderData}: Route.ComponentProps) {
  return <BagPage limit={loaderData.limit} />;
}
