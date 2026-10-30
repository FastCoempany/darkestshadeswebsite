import {forwardRef, type ButtonHTMLAttributes} from 'react';
import {Link} from 'react-router';
import {cx} from '~/lib/cx';

export type ButtonVariant = 'solid' | 'outline' | 'quiet';
export type ButtonSize = 40 | 48 | 56;

const VARIANT: Record<ButtonVariant, string> = {
  solid:
    'bg-ds-action-primary-bg text-ds-action-primary-text hover:bg-ds-action-primary-bg-hover active:bg-ds-action-primary-bg uppercase tracking-micro text-ui',
  outline:
    'border border-ds-action-secondary-border text-ds-action-secondary-text hover:bg-ds-surface-raised active:bg-ds-surface-overlay uppercase tracking-micro text-ui',
  quiet: 'text-ds-action-quiet-text hover:text-ds-action-quiet-text-hover hover:underline underline-offset-3 text-ui',
};

const SIZE: Record<ButtonSize, string> = {
  // 40 px tall, with a 44 px hit area (05, Behavior rules).
  40: "h-10 px-4 relative before:absolute before:-inset-y-0.5 before:inset-x-0 before:content-['']",
  48: 'h-12 px-6',
  56: 'h-14 px-8',
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Working: the label stays, the control is inert and announced busy. */
  busy?: boolean;
  /** Renders a link that looks like a button. */
  to?: string;
  full?: boolean;
}

/**
 * Square corners, Stolzl Medium, never gold-filled (docs/brief/05-components.md). `solid` is bone on
 * night and onyx on paper through the action tokens; `quiet` is text only with an underline on hover.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {variant = 'solid', size = 48, busy = false, to, full = false, className, children, disabled, type = 'button', ...rest},
  ref,
) {
  const classes = cx(
    'inline-flex items-center justify-center gap-2 font-text font-medium leading-none rounded-none select-none',
    'transition-colors duration-(--motion-quick) motion-reduce:transition-none',
    'disabled:text-ds-text-disabled disabled:bg-ds-surface-raised disabled:border-ds-border-hairline disabled:cursor-not-allowed',
    'aria-busy:cursor-progress',
    VARIANT[variant],
    variant === 'quiet' ? 'min-h-11 px-0' : SIZE[size],
    full && 'w-full',
    className,
  );
  if (to) {
    const {onClick, ...anchorRest} = rest as React.AnchorHTMLAttributes<HTMLAnchorElement> & Record<string, unknown>;
    // Another origin (the checkout at launch) is a plain anchor; the site's own paths are router links.
    if (/^https?:\/\//.test(to)) {
      return (
        <a href={to} className={classes} aria-disabled={disabled || undefined} {...anchorRest}>
          {children}
        </a>
      );
    }
    return (
      <Link to={to} className={classes} aria-disabled={disabled || undefined} {...anchorRest}>
        {children}
      </Link>
    );
  }
  // Busy keeps its place in the tab order: aria-disabled, clicks ignored.
  return (
    <button
      ref={ref}
      type={type}
      className={classes}
      disabled={disabled}
      aria-busy={busy || undefined}
      aria-disabled={busy || undefined}
      {...rest}
      onClick={busy ? (e) => e.preventDefault() : rest.onClick}
    >
      {children}
    </button>
  );
});
