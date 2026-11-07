// The wall, alone (DRAWER-WALL.md). D1: the project and its placeholders; the elements land in D5 and D6.
import './styles/fonts.css';
import './styles/base.css';

declare global {
  interface Window { __wall?: { phase: string } }
}
window.__wall = { phase: 'D1' };
