/**
 * The cast: seven people (W1, W2, W3, M1, M2, M3, NB) and the twenty planned on-model pictures in
 * content/photography/people/*.json. A `final` has a web export in the manifest; a `draft` stays a
 * labelled slot (RUN.md, Where things stand).
 */
import {imageById} from './manifest';
import type {CastId, CastMember, CastShot, FrameId, SceneId} from './types';

interface CastShotFile {
  id: string;
  cast: string;
  scene: string;
  frame: string;
  angle: string;
  wardrobe: string;
  format: string;
  status: string;
}

const files = import.meta.glob('../../../content/photography/people/*.json', {
  eager: true,
  import: 'default',
}) as Record<string, CastShotFile>;

export const CAST_ORDER: CastId[] = ['W1', 'W2', 'W3', 'M1', 'M2', 'M3', 'NB'];

/** One picture per person on /cast: their studio shot (RUN.md, Edge cases). */
const PORTRAITS: Record<CastId, string> = {
  W1: 'W1-S07-F02-A1',
  W2: 'W2-S06-F03-A1',
  W3: 'W3-S02-F09-A1',
  M1: 'M1-S06-F04-A1',
  M2: 'M2-S07-F01-A1',
  M3: 'M3-S02-F02-A1',
  NB: 'NB-S06-F06-A1',
};

function toShot(path: string, file: CastShotFile): CastShot {
  const code = path.split('/').pop()!.replace(/\.json$/, '');
  const manifestId = file.id.replace(/-v\d+$/, '').toLowerCase();
  const status = file.status === 'final' ? 'final' : 'draft';
  return {
    code,
    cast: file.cast as CastId,
    scene: file.scene as SceneId,
    frame: file.frame as FrameId,
    angle: file.angle === 'A2' ? 'A2' : 'A1',
    wardrobe: file.wardrobe,
    ratio: 'stage',
    ratioLabel: '4:5',
    status,
    manifestId: status === 'final' ? manifestId : null,
    image: status === 'final' ? imageById(manifestId) : null,
  };
}

export const shots: CastShot[] = Object.entries(files)
  .map(([path, file]) => toShot(path, file))
  .sort((a, b) => a.code.localeCompare(b.code));

export const members: CastMember[] = CAST_ORDER.map((id) => ({
  id,
  portrait: shots.find((s) => s.code === PORTRAITS[id]) ?? null,
  shots: shots.filter((s) => s.cast === id),
}));

export function shotsForFrame(frame: FrameId): CastShot[] {
  return shots.filter((s) => s.frame === frame);
}
