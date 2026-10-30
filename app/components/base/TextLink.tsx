import type {ComponentProps} from 'react';
import {Link, NavLink, useLocation} from 'react-router';
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
  const prefixed = activePrefix ? pathname === activePrefix || pathname.startsWith(`${activePrefix}s/`) || pathname.startsWith(`${activePrefix}/`) : false;
  if (external) {
    return (
      <a href={String(to)} className={classes} target="_blank" rel="noreferrer">
        {children}
      </a>
    );
  }
  if (variant === 'nav') {
    return (
      <NavLink to={to} className={classes} aria-current={prefixed ? 'page' : undefined} {...rest}>
        {children}
      </NavLink>
    );
  }
  return (
    <Link to={to} className={classes} {...rest}>
      {children}
    </Link>
  );
}
