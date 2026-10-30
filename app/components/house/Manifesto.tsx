import {cx} from '~/lib/cx';

export interface ManifestoProps {
  /** The huge lines, one per screen on a phone. */
  lines: string[];
  /** Numbered body paragraphs (the manifesto page). */
  paragraphs?: string[];
  variant?: 'home' | 'page' | 'print';
  className?: string;
}

/** Stacked statements in Owners Wide; type does the work a campaign photo would (docs/brief/02). */
export function Manifesto({lines, paragraphs = [], variant = 'home', className}: ManifestoProps) {
  return (
    <div className={cx('grid', className)} data-manifesto={variant}>
      {lines.map((line) => (
        <p
          key={line}
          className={cx(
            'ds-display text-manifesto leading-manifesto tracking-display text-ds-text-primary',
            variant === 'home' ? 'grid min-h-dvh place-items-center px-4 py-16 text-center md:px-6 lg:px-10 xl:px-14' : 'py-6',
          )}
        >
          {line}
        </p>
      ))}
      {paragraphs.length ? (
        <ol className="ds-measure grid gap-8 py-12">
          {paragraphs.map((p, i) => (
            <li key={p} className="grid grid-cols-[2.5rem_1fr] gap-4">
              <span className="ds-tabular pt-1 font-text text-micro font-medium uppercase tracking-micro text-ds-text-editorial">{String(i + 1).padStart(2, '0')}</span>
              <p className="font-text text-body-lg font-book leading-body text-ds-text-primary">{p}</p>
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}
