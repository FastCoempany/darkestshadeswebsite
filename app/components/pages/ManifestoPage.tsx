import {Manifesto} from '~/components/house/Manifesto';
import {copy} from '~/lib/copy';

/**
 * Paper theme, frontal and centred like the other paper pages: the label, the statement across the page's
 * content width (the one line is never cut), then the numbered paragraphs in a centred reading measure.
 */
export function ManifestoPage() {
  const paragraphs = copy.manifesto.paragraphs;
  const statement = paragraphs[paragraphs.length - 1];
  return (
    <main id="main" className="grid gap-12 px-4 py-16 md:px-6 lg:px-10 xl:px-14" data-page="manifesto">
      <h1 className="ds-display text-center text-label leading-ui tracking-label text-ds-text-secondary">{copy.manifesto.title}</h1>
      <Manifesto lines={[statement]} paragraphs={paragraphs.slice(0, -1)} variant="page" />
    </main>
  );
}
