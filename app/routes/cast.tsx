import type {Route} from './+types/cast';
import {CastPage} from '~/components/pages/CastPage';
import {copy, pageMeta} from '~/lib/copy';

export const meta: Route.MetaFunction = () => pageMeta(copy.cast.title);

export async function loader({context}: Route.LoaderArgs) {
  return {members: context.store.cast.members(), products: context.store.products.all()};
}

export default function Cast({loaderData}: Route.ComponentProps) {
  return <CastPage {...loaderData} />;
}
