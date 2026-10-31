import {cx} from '~/lib/cx';

/** The small centered sentence with a period that cuts on and off (03, reference 1). Night or black ground. */
export function Card({text, ground = 'night', className}: {text: string; ground?: 'night' | 'black'; className?: string}) {
  return (
    <div className={cx('grid h-full w-full place-items-center px-6 text-center', ground === 'black' ? 'bg-ds-surface-entry' : 'bg-ds-surface-overlay', className)} data-card={ground}>
      <p className="font-text text-card font-regular leading-ui text-ds-text-primary">{text}</p>
    </div>
  );
}
