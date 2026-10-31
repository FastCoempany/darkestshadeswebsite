import {useNonce} from '@shopify/hydrogen';
import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  isRouteErrorResponse,
  useMatches,
  useRouteError,
  useRouteLoaderData,
  type ShouldRevalidateFunction,
} from 'react-router';
import type {Route} from './+types/root';
import tailwindCss from '~/styles/tailwind.css?url';
import monaSans from '@fontsource-variable/mona-sans/standard.css?url';
import urbanist from '@fontsource-variable/urbanist/index.css?url';
import localFonts from '~/styles/fonts.local.css?url';
import faviconSvg from '../brand/marks/favicon/favicon.svg?url';
import faviconIco from '../brand/marks/favicon/favicon.ico?url';
import appleTouch from '../brand/marks/favicon/apple-touch-icon.png?url';
import {NotFoundPage} from '~/components/pages/NotFoundPage';
import {PageShell} from '~/components/house/PageShell';
import {CartProvider} from '~/lib/cart';
import {currentDropView} from '~/lib/drop-view';
import {copy, pageTitle} from '~/lib/copy';
import {MODE_COOKIE, readCookie} from '~/lib/cookies';

export type RootLoader = typeof loader;

/** Root data only changes after a mutation; sub-navigations keep it. */
export const shouldRevalidate: ShouldRevalidateFunction = ({formMethod, currentUrl, nextUrl}) => {
  if (formMethod && formMethod !== 'GET') return true;
  if (currentUrl.toString() === nextUrl.toString()) return true;
  return false;
};

/** The favicon set is the brand mark, never the GCD (00-decisions.md #11). No preconnects to Shopify in this phase. */
export function links() {
  return [
    {rel: 'icon', type: 'image/svg+xml', href: faviconSvg},
    {rel: 'icon', sizes: '48x48', href: faviconIco},
    {rel: 'apple-touch-icon', href: appleTouch},
  ];
}

export const meta: Route.MetaFunction = () => [
  {title: pageTitle()},
  {name: 'description', content: copy.meta.defaultDescription},
];

export async function loader({request, context}: Route.LoaderArgs) {
  const url = new URL(request.url);
  const cookie = request.headers.get('Cookie');
  const wire = url.searchParams.get('mode') === 'wire' || readCookie(cookie, MODE_COOKIE) === 'wire';
  return {
    mode: wire ? ('wire' as const) : ('ui' as const),
    adobeFontsKit: context.settings.adobeFontsKit,
    reviewBuild: context.settings.reviewBuild,
    drop: currentDropView(context),
    year: context.now.getFullYear(),
  };
}

/** Routes opt into the paper theme for long reading with `export const handle = {theme: 'paper'}`. */
export type RouteHandle = {theme?: 'night' | 'paper'; headerSurface?: 'transparent' | 'solid'; footerList?: boolean; dropLine?: boolean; listOffer?: boolean};

export function Layout({children}: {children?: React.ReactNode}) {
  const nonce = useNonce();
  const data = useRouteLoaderData<RootLoader>('root');
  const matches = useMatches();
  const theme = [...matches].reverse().find((m) => (m.handle as RouteHandle | undefined)?.theme)?.handle as RouteHandle | undefined;
  const realFonts = Boolean(data?.adobeFontsKit) || import.meta.env.DS_LOCAL_FONTS === '1';

  return (
    <html lang="en" data-theme={theme?.theme ?? 'night'} data-mode={data?.mode === 'wire' ? 'wire' : undefined}>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <link rel="stylesheet" href={tailwindCss} />
        {data?.adobeFontsKit ? <link rel="stylesheet" href={`https://use.typekit.net/${data.adobeFontsKit}.css`} /> : null}
        {import.meta.env.DS_LOCAL_FONTS === '1' ? <link rel="stylesheet" href={localFonts} /> : null}
        {realFonts ? null : (
          <>
            <link rel="stylesheet" href={monaSans} />
            <link rel="stylesheet" href={urbanist} />
          </>
        )}
        <Meta />
        <Links />
      </head>
      <body className="min-h-dvh bg-ds-surface-canvas text-ds-text-primary">
        {children}
        <ScrollRestoration nonce={nonce} />
        <Scripts nonce={nonce} />
      </body>
    </html>
  );
}

export default function App() {
  const data = useRouteLoaderData<RootLoader>('root');
  const matches = useMatches();
  const handles = matches.map((m) => m.handle as RouteHandle | undefined);
  const headerSurface = [...handles].reverse().find((h) => h?.headerSurface)?.headerSurface ?? 'solid';
  const footerList = [...handles].reverse().find((h) => h?.footerList !== undefined)?.footerList ?? true;
  const dropLine = [...handles].reverse().find((h) => h?.dropLine !== undefined)?.dropLine ?? true;
  const listOffer = [...handles].reverse().find((h) => h?.listOffer !== undefined)?.listOffer ?? false;
  return (
    <CartProvider>
      <PageShell drop={data?.drop ?? null} year={data?.year ?? 2026} headerSurface={headerSurface} showFooterList={footerList} showDropLine={dropLine} listOffer={listOffer}>
        <Outlet />
      </PageShell>
    </CartProvider>
  );
}

export function ErrorBoundary() {
  const error = useRouteError();
  const data = useRouteLoaderData<RootLoader>('root');
  const status = isRouteErrorResponse(error) ? error.status : 500;
  if (!isRouteErrorResponse(error)) console.error(error);
  return (
    <CartProvider>
      <PageShell drop={data?.drop ?? null} year={data?.year ?? 2026}>
        <NotFoundPage status={status} />
      </PageShell>
    </CartProvider>
  );
}
