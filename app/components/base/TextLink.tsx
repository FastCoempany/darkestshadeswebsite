import type {ComponentProps} from 'react';
import {Link, useLocation} from 'react-router';
import {copy} from '~/lib/copy';
import {cx} from '~/lib/cx';

export type TextLinkVariant = 'inline' | 'nav' | 'footer';

const VARIANT: Record<TextLinkVariant, string> = {
  inline: 'underline decoration-1 underline-offset-3 hover:decoration-2',
  nav: 'inline-flex min-h-11 items-center font-text text-ui font-medium hover:underline underline-offset-3 aria-[current=page]:underline',
  footer: 'inline-flex min-h-11 items-center font-text text-small text-ds-text-secondary hover:text-ds-text-primary hover:underline underline-offset-3',
};

export interface TextLinkProps extends Omit<ComponentProps<typeof Link>, 'className'> {
  variant?: TextLinkVariant;
  className?: string;
  /** External link (Instagram): a plain anchor, opened in a new tab. */
  external?: boolean;
  /** Nav links: also current when the path starts with this (`/drop` covers `/drops/001`). */
  activePrefix?: string;
}

/** Inline links are underlined, 1 px, 3 px off (docs/brief/05-components.md). Nav links mark the current page. */
export function TextLink({variant = 'inline', className, external = false, activePrefix, to, children, ...rest}: TextLinkProps) {
  const classes = cx('rounded-none', VARIANT[variant], className);
  const {pathname} = useLocation();
  const target = String(to);
  const active = activePrefix ? pathname === activePrefix || pathname.startsWith(`${activePrefix}s/`) || pathname.startsWith(`${activePrefix}/`) : pathname === target;
  if (external) {
    const {reloadDocument: _r, replace: _p, state: _s, preventScrollReset: _ps, relative: _rel, viewTransition: _v, ...anchorRest} = rest;
    return (
      <a href={target} className={classes} target="_blank" rel="noreferrer" {...(anchorRest as React.AnchorHTMLAttributes<HTMLAnchorElement>)}>
        {children}
        <span className="sr-only"> ({copy.nav.opensInNewTab})</span>
      </a>
    );
  }
  return (
    <Link to={to} className={classes} aria-current={variant === 'nav' && active ? 'page' : undefined} {...rest}>
      {children}
    </Link>
  );
}
