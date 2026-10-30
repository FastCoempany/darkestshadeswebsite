import type {Route} from './+types/frames.$handle';
import gcdRender from '../../brand/emblems/gcd/render/gcd-3d-yaw35-1024.png?url';
import {FramePage} from '~/components/pages/FramePage';
import {copy, fill, pageTitle} from '~/lib/copy';
import {currentDropView} from '~/lib/drop-view';

export const meta: Route.MetaFunction = ({data}) => [
  {title: pageTitle(data?.product.title)},
  {name: 'description', content: data ? fill(copy.alt.stage, {subject: copy.alt.subjects[data.product.ds.id], angle: copy.alt.angles.A1}) : copy.meta.defaultDescription},
];

export async function loader({params, context}: Route.LoaderArgs) {
  const product = context.store.products.byHandle(params.handle);
  if (!product) throw new Response('Not found', {status: 404});
  return {
    product,
    drop: currentDropView(context),
    castShots: context.store.cast.shotsForFrame(product.ds.id),
    next: context.store.products.next(product.ds.id),
    // F08's pictures show no GCD: its detail hold uses the emblem's render (RUN.md, Edge cases).
    detailRender: product.ds.id === 'F08' ? gcdRender : null,
  };
}

export default function Frame({loaderData}: Route.ComponentProps) {
  return <FramePage {...loaderData} />;
}
