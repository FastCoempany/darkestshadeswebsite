import {useId} from 'react';

/**
 * A 3–4% film grain over photography only, never over the interface (01-brand-system.md, patina). An SVG
 * noise layer, switched off under prefers-reduced-transparency and for product cut-outs (callers leave
 * it off there). Renders inside a ShotSlot (the slot is `relative`).
 */
export function FilmGrain({on = true}: {on?: boolean}) {
  const id = useId();
  if (!on) return null;
  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.035] mix-blend-screen reduced-transparency:hidden" aria-hidden="true" data-film-grain>
      <filter id={id}>
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter={`url(#${id})`} />
    </svg>
  );
}
