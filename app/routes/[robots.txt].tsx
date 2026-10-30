import type {Route} from './+types/[robots.txt]';

export function loader(_args: Route.LoaderArgs) {
  const body = ['User-agent: *', 'Disallow: /cart', 'Disallow: /account', 'Disallow: /dev/', ''].join('\n');
  return new Response(body, {
    status: 200,
    headers: {'Content-Type': 'text/plain', 'Cache-Control': `max-age=${60 * 60 * 24}`},
  });
}
