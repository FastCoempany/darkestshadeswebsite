import type {Route} from './+types/dev.tokens';
import {TokenSheet} from '~/components/dev/TokenSheet';
import {pageTitle} from '~/lib/copy';

export const meta: Route.MetaFunction = () => [{title: pageTitle('Tokens')}, {name: 'robots', content: 'noindex'}];

/** The token test page (09-build-plan.md, phase 0). Dev server and review builds only; a production build 404s it. */
export async function loader({context}: Route.LoaderArgs) {
  if (!import.meta.env.DEV && !context.settings.reviewBuild) {
    throw new Response('Not found', {status: 404});
  }
  return {
    frames: context.store.products.all().map((p) => ({id: p.ds.id, look: p.ds.lookNumber, name: p.title, image: p.featuredImage})),
    hero: context.store.images.forShot('F09', 'H'),
  };
}

export default function DevTokens({loaderData}: Route.ComponentProps) {
  return <TokenSheet frames={loaderData.frames} hero={loaderData.hero} />;
}
