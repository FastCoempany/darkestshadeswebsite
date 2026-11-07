/// <reference types="vite/client" />
declare module 'virtual:wall-frames' {
  import type { FrameFacts, FrameId } from './lib/types';
  const frames: Partial<Record<FrameId, FrameFacts>>;
  export default frames;
}
declare module 'virtual:wall-copy' {
  import type { WallCopy } from './data/extract';
  const copy: WallCopy;
  export default copy;
}
