// A focus trap for the drawer view (role="dialog", aria-modal): Tab cycles inside it, focus starts on the first
// control, and release gives focus back to where it came from (the drawer on the wall). The root may live in a
// shadow tree, and the controls inside it may live in nested shadow trees (<photo-zoom>'s buttons, <lifted-frame>'s
// canvas): the focusable list is collected through open shadow roots in tree order, the active element is read
// down through the shadow roots that hold it, and a focus event's real target comes from its composed path.

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export interface FocusTrap {
  release(): void;
}

/** Whether `node` is inside `root`, through shadow boundaries (an element's own `contains` stops at them). */
export function within(root: Node, node: Node | null): boolean {
  let n: Node | null = node;
  while (n) {
    if (n === root) return true;
    n = n.parentNode ?? (n instanceof ShadowRoot ? n.host : null);
  }
  return false;
}

/** The element with focus, seen from inside `root`'s tree and down through nested shadow roots: a shadow root's
 * own activeElement is the host of the next tree when focus sits deeper, so the walk continues into it. */
export function activeIn(root: HTMLElement): Element | null {
  const tree = root.getRootNode();
  let a: Element | null = tree instanceof ShadowRoot ? tree.activeElement : document.activeElement;
  while (a?.shadowRoot?.activeElement) a = a.shadowRoot.activeElement;
  return a;
}

/** Every focusable element under `root` in tree order, through open shadow roots (querySelectorAll stops at them). */
export function focusablesIn(root: ParentNode): HTMLElement[] {
  const out: HTMLElement[] = [];
  const walk = (node: ParentNode) => {
    for (const el of node.children) {
      if (el.matches(FOCUSABLE)) out.push(el as HTMLElement);
      if (el.shadowRoot) walk(el.shadowRoot);
      walk(el);
    }
  };
  walk(root);
  return out;
}

export function trapFocus(root: HTMLElement, initial?: HTMLElement | null): FocusTrap {
  const from = (activeIn(root) ?? document.activeElement) as HTMLElement | null;
  const focusables = () => focusablesIn(root).filter((el) => !el.hidden && (el.offsetParent !== null || el === activeIn(root)));
  const onKey = (ev: KeyboardEvent) => {
    if (ev.key !== 'Tab') return;
    const list = focusables();
    if (!list.length) { ev.preventDefault(); root.focus(); return; }
    const first = list[0]!, last = list[list.length - 1]!;
    const active = activeIn(root);
    if (ev.shiftKey && (active === first || !within(root, active))) { ev.preventDefault(); last.focus(); }
    else if (!ev.shiftKey && (active === last || !within(root, active))) { ev.preventDefault(); first.focus(); }
  };
  const onFocusIn = (ev: FocusEvent) => {
    const target = (ev.composedPath()[0] ?? ev.target) as Node | null;
    if (target && !within(root, target)) {
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
