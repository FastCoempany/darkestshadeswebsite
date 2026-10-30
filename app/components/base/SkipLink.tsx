/** Skip to content, first in the tab order on every page; visible on focus. */
export function SkipLink({href = '#main', children}: {href?: string; children: string}) {
  return (
    <a
      href={href}
      className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-(--z-toast) focus:bg-ds-action-primary-bg focus:px-4 focus:py-3 focus:font-text focus:text-ui focus:font-medium focus:text-ds-action-primary-text"
    >
      {children}
    </a>
  );
}
