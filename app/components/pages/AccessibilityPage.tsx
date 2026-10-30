import {Form} from 'react-router';
import {Button} from '~/components/base/Button';
import {Notice} from '~/components/base/Notice';
import {ReadingPage} from '~/components/pages/ReadingPage';
import {copy, fill} from '~/lib/copy';

export interface AccessibilityPageProps {
  /** Whether the opening sequence is on for this visitor. */
  introOn: boolean;
  saved?: boolean;
  /** The sentence with {supportEmail} stays hidden until there is an address (RUN.md, Edge cases). */
  supportEmail?: string | null;
}

/** The accessibility statement, the photosensitivity note, and the switch that turns the intro off. */
export function AccessibilityPage({introOn, saved = false, supportEmail = null}: AccessibilityPageProps) {
  return (
    <ReadingPage title={copy.accessibility.title}>
      {copy.accessibility.body.map((p) => {
        const text = fill(p, {supportEmail});
        return text ? <p key={p}>{text}</p> : null;
      })}
      <Form method="post" className="grid gap-4 border-t border-ds-border-hairline pt-8" aria-labelledby="intro-toggle">
        <h2 id="intro-toggle" className="ds-display text-label leading-ui tracking-label text-ds-text-secondary">
          {copy.accessibility.introToggle.label}
        </h2>
        <div className="flex flex-wrap gap-3" role="group" aria-labelledby="intro-toggle">
          <Button type="submit" name="intro" value="on" variant={introOn ? 'solid' : 'outline'} size={48} aria-pressed={introOn}>
            {copy.accessibility.introToggle.on}
          </Button>
          <Button type="submit" name="intro" value="off" variant={introOn ? 'outline' : 'solid'} size={48} aria-pressed={!introOn}>
            {copy.accessibility.introToggle.off}
          </Button>
        </div>
        {saved ? <Notice tone="success">{copy.accessibility.introToggle.saved}</Notice> : null}
      </Form>
    </ReadingPage>
  );
}
