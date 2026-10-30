import type {ElementType, ReactNode} from 'react';

/** Text for assistive technology only. */
export function VisuallyHidden({as: Tag = 'span', children}: {as?: ElementType; children: ReactNode}) {
  return <Tag className="sr-only">{children}</Tag>;
}
