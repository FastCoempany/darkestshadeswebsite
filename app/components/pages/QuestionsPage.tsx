import {Disclosure} from '~/components/base/Disclosure';
import {ReadingPage} from '~/components/pages/ReadingPage';
import {copy} from '~/lib/copy';

export function QuestionsPage() {
  return (
    <ReadingPage title={copy.questions.title}>
      <div className="border-b border-ds-border-hairline">
        {copy.questions.items.map((item, i) => (
          <Disclosure key={item.q} summary={item.q} id={`q-${i + 1}`} open={i === 0}>
            <p>{item.a}</p>
          </Disclosure>
        ))}
      </div>
    </ReadingPage>
  );
}
