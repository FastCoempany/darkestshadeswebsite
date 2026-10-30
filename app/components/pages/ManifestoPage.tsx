import {Manifesto} from '~/components/house/Manifesto';
import {copy} from '~/lib/copy';

/** Paper theme. The full statement: the last paragraph is the tagline, set as a statement. */
export function ManifestoPage() {
  const paragraphs = copy.manifesto.paragraphs;
  const statement = paragraphs[paragraphs.length - 1];
  return (
    <main id="main" className="mx-auto grid max-w-4xl gap-12 px-4 py-16 md:px-6 lg:px-10" data-page="manifesto">
      <h1 className="ds-display text-label leading-ui tracking-label text-ds-text-secondary">{copy.manifesto.title}</h1>
      <Manifesto lines={[statement]} paragraphs={paragraphs.slice(0, -1)} variant="page" />
    </main>
  );
}
