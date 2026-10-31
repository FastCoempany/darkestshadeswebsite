import type {Route} from './+types/frames._index';
import {FramesPage} from '~/components/pages/FramesPage';
import {copy, pageMeta} from '~/lib/copy';
import {currentDropView} from '~/lib/drop-view';

export const meta: Route.MetaFunction = () => pageMeta(copy.frames.title, copy.frames.statement);

export async function loader({context}: Route.LoaderArgs) {
  return {products: context.store.products.all(), drop: currentDropView(context)};
}

export default function Frames({loaderData}: Route.ComponentProps) {
  return <FramesPage {...loaderData} />;
}
