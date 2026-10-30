import {isbot} from 'isbot';
import type {Route} from './+types/_index';
import {HomePage} from '~/components/pages/HomePage';
import {copy, pageTitle} from '~/lib/copy';
import {currentDropView} from '~/lib/drop-view';
import {shouldShowEntry} from '~/lib/entry';
import {MODE_COOKIE, readCookie} from '~/lib/cookies';

export const meta: Route.MetaFunction = () => [
  {title: pageTitle()},
  {name: 'description', content: copy.meta.defaultDescription},
];

/** The home page has its own list section, so the footer's is left out. */
export const handle = {headerSurface: 'transparent', footerList: false};

export async function loader({request, context}: Route.LoaderArgs) {
  const {store} = context;
  const url = new URL(request.url);
  const wire = url.searchParams.get('mode') === 'wire' || readCookie(request.headers.get('Cookie'), MODE_COOKIE) === 'wire';
  return {
    products: store.products.all(),
    drop: currentDropView(context),
    cast: store.cast.members(),
    detail: store.images.forShot('F09', 'A6'),
    dropHero: store.images.forShot('F09', 'H'),
    showEntry: shouldShowEntry(request, isbot(request.headers.get('user-agent'))),
    wire,
  };
}

export default function Home({loaderData}: Route.ComponentProps) {
  return <HomePage {...loaderData} />;
}
