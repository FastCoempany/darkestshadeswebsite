import type {Route} from './+types/$';
import {copy, pageTitle} from '~/lib/copy';

export const meta: Route.MetaFunction = () => [{title: pageTitle(copy.notFound.title)}];

/** Any other path: one line, the brand mark, a way back (the root ErrorBoundary renders it). */
export async function loader({request}: Route.LoaderArgs) {
  throw new Response(`${new URL(request.url).pathname} not found`, {status: 404});
}

export default function CatchAllPage() {
  return null;
}
