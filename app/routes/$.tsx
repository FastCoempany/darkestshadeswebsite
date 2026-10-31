import type {Route} from './+types/$';

/** Any other path: one line, the brand mark, a way back (the root ErrorBoundary renders it and the root's meta titles it). */
export async function loader({request}: Route.LoaderArgs) {
  throw new Response(`${new URL(request.url).pathname} not found`, {status: 404});
}

export default function CatchAllPage() {
  return null;
}
