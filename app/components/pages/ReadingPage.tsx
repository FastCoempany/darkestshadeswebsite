import type {ReactNode} from 'react';
import {cx} from '~/lib/cx';

/** Paper theme, long-reading layout, lines no longer than 68 characters, anchored headings (04). */
export function ReadingPage({title, children, className, id = 'main'}: {title: string; children: ReactNode; className?: string; id?: string}) {
  return (
    <main id={id} className={cx('mx-auto grid w-full max-w-3xl gap-10 px-4 py-16 md:px-6', className)} data-page="reading">
      <h1 className="ds-display text-h1 leading-heading tracking-heading">{title}</h1>
      <div className="ds-measure grid gap-8 font-text text-body leading-body text-ds-text-primary">{children}</div>
    </main>
  );
}
