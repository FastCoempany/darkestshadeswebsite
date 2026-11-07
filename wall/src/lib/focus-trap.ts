// A focus trap for the drawer view (role="dialog", aria-modal): Tab cycles inside it, focus starts on the first
// control, and release gives focus back to where it came from (the drawer on the wall).

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export interface FocusTrap {
  release(): void;
}

export function trapFocus(root: HTMLElement, initial?: HTMLElement | null): FocusTrap {
  const from = document.activeElement as HTMLElement | null;
  const focusables = () => [...root.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((el) => el.offsetParent !== null || el === document.activeElement);
  const onKey = (ev: KeyboardEvent) => {
    if (ev.key !== 'Tab') return;
    const list = focusables();
    if (!list.length) { ev.preventDefault(); root.focus(); return; }
    const first = list[0]!, last = list[list.length - 1]!;
    const active = document.activeElement;
    if (ev.shiftKey && (active === first || !root.contains(active))) { ev.preventDefault(); last.focus(); }
    else if (!ev.shiftKey && (active === last || !root.contains(active))) { ev.preventDefault(); first.focus(); }
  };
  const onFocusIn = (ev: FocusEvent) => {
    if (!root.contains(ev.target as Node)) {
      const list = focusables();
      (list[0] ?? root).focus();
    }
  };
  root.addEventListener('keydown', onKey);
  document.addEventListener('focusin', onFocusIn);
  const target = initial ?? focusables()[0] ?? root;
  queueMicrotask(() => target.focus({ preventScroll: true }));
  return {
    release() {
      root.removeEventListener('keydown', onKey);
      document.removeEventListener('focusin', onFocusIn);
      if (from && from.isConnected) from.focus({ preventScroll: true });
    },
  };
}
