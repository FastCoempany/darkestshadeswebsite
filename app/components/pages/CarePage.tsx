import {ReadingPage} from '~/components/pages/ReadingPage';
import {copy} from '~/lib/copy';

/** Care is a placeholder until the factory confirms it; review builds show it as it is (RUN.md). */
export function CarePage() {
  return (
    <ReadingPage title={copy.care.title}>
      <p className="text-ds-text-secondary">{copy.care.body}</p>
    </ReadingPage>
  );
}
