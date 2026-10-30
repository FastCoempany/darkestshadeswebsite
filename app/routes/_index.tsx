import type {Route} from './+types/_index';
import {copy, pageTitle} from '~/lib/copy';

export const meta: Route.MetaFunction = () => [
  {title: pageTitle()},
  {name: 'description', content: copy.meta.defaultDescription},
];

/**
 * Phase 0 placeholder for the home page: the three manifesto lines, one per screen on a phone.
 * Phase 1 replaces it with the full template (docs/brief/04-ia-and-pages.md).
 */
export default function Home() {
  return (
    <main id="main">
      {copy.home.manifesto.map((line) => (
        <section key={line} className="grid min-h-dvh place-items-center px-4 py-16 text-center md:px-6 lg:px-10 xl:px-14">
          <p className="ds-display text-manifesto leading-manifesto tracking-display">{line}</p>
        </section>
      ))}
    </main>
  );
}
