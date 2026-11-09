// The iOS-safe scroll lock (DRAWER-WALL.md, Interaction constants): while the drawer view is open nothing behind it
// scrolls. The body is fixed at its scroll position (the only lock Safari honours), and restored on release.

let locked = false;
let scrollY = 0;
let saved: { position: string; top: string; left: string; right: string; width: string; overflow: string } | null = null;

export function lockScroll(): void {
  if (locked) return;
  locked = true;
  scrollY = window.scrollY;
  const s = document.body.style;
  saved = { position: s.position, top: s.top, left: s.left, right: s.right, width: s.width, overflow: s.overflow };
  s.position = 'fixed';
  s.top = `-${scrollY}px`;
  s.left = '0';
  s.right = '0';
  s.width = '100%';
  s.overflow = 'hidden';
}

export function unlockScroll(): void {
  if (!locked) return;
  locked = false;
  const s = document.body.style;
  if (saved) {
    s.position = saved.position;
    s.top = saved.top;
    s.left = saved.left;
    s.right = saved.right;
    s.width = saved.width;
    s.overflow = saved.overflow;
  }
  saved = null;
  window.scrollTo(0, scrollY);
}

export function scrollLocked(): boolean {
  return locked;
}
