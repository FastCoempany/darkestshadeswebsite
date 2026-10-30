/** Skip to content, first in the tab order on every page; visible on focus. */
export function SkipLink({href = '#main', children, ...rest}: {href?: string; children: string} & Record<`data-${string}`, string | undefined>) {
  return (
    <a
      href={href}
      {...rest}
      className="sr-only focus-visible:not-sr-only focus-visible:fixed focus-visible:top-2 focus-visible:left-2 focus-visible:z-(--z-toast) focus-visible:bg-ds-action-primary-bg focus-visible:px-4 focus-visible:py-3 focus-visible:font-text focus-visible:text-ui focus-visible:font-medium focus-visible:text-ds-action-primary-text"
    >
      {children}
    </a>
  );
}
