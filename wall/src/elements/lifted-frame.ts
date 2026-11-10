// <lifted-frame> (DRAWER-WALL.md, steps 4 and 5, In the browser): the live 3D frame, three.js inside, loaded on the
// first open and never in the initial bundle. One canvas, rendered only while something changes, AgX tone mapping,
// the drawer's own HDR as the environment plus one warm key matched to the scene. The handoff: the canvas mounts
// over the drawer's last frame with the GLB at open.json's transform and a soft contact shadow, cross-fades over
// 120 ms, then springs to the inspect pose; turning (one finger, about any axis, #48), pinching and the wheel report
// deltas up to the view, whose machine holds the pose; the view forwards the pointer events of its whole screen here
// while the frame is rising or lifted, so the finger may start anywhere but the buttons. Tier 1 shows the lifted still instead, and never loads three.js: the library and its
// loaders are imported inside setup(), which runs at tier 2 only. On a lost context: tier 1 for the rest of the visit.
// `lifted-handoff` tells the view when the frame fades in and out, so the empty drawer behind it fades with it.
import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { classMap } from 'lit/directives/class-map.js';
import type * as THREE from 'three';
import type { WallStore } from '../data/store';
import type { FrameFacts } from '../lib/types';
import type { Tier } from '../lib/tier';
import { HANDOFF_FADE_MS, IDENTITY_ROT, INERTIA_FRICTION, LIFT_MS, LIFT_REDUCED_MS, clampZoom, isLiftedTap, pinchZoom, doubleTapZoom, wheelZoom, TAP_MAX_MS, type Quat } from '../lib/gestures';
import { springStep, springSettled, type SpringState } from '../lib/spring';
import { log } from '../lib/log';

export interface Pose { rot: Quat; zoom: number }
interface FramePose { matrix_three: number[][] }
// camera/open.json and inspect.json: the camera, every frame's pose under `frames` (the default frame's again as `frame`)
interface CameraJson { camera: { three: { position: number[]; fov_deg: number; near: number; far: number; quaternion_xyzw: number[] } }; frame: FramePose; frames?: Record<string, FramePose> }

const LIFT_SPRING = { stiffness: 120, damping: 20 };
/** The zoom from which the fit no longer moves the frame (whole at 1x, fading to nothing here). */
const FIT_ZOOM_MAX = 1.25;

/** three.js and the loaders (lifted-three.ts: the named pieces the live frame uses), loaded once at the first tier-2
 * lift into their own chunk, never in the initial bundle; null until the first setup has run (the pose math needs it). */
type ThreeModule = typeof import('./lifted-three');
let T: ThreeModule | null = null;
const loadThree = (): Promise<ThreeModule> => import('./lifted-three');
/** The environment map's turn (DRAWER-WALL.md, The drawer view; the env entry's `threeRotation`): Blender's
 * equirectangular camera put its forward (+y Blender, -z here) at the image's centre column and the camera's right
 * (+x) three quarters across, which three.js's equirectangular mapping shows a quarter turn away; turned +90 degrees
 * about the vertical, a probe capture (three emissive markers: right, up, ahead) reads back in its own directions
 * as the scene's background and in a mirror sphere's reflections (D5). */
const ENV_ROTATION_Y = Math.PI / 2;

@customElement('lifted-frame')
export class LiftedFrame extends LitElement {
  static override styles = css`
    :host { display: block; position: absolute; inset: 0; touch-action: none; }
    canvas, img { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
    img { object-fit: cover; }
    .fade { opacity: 0; transition: opacity 120ms var(--motion-ease); }
    .fade.in { opacity: 1; }
    .still.in { transition-duration: 200ms; }
    .live { cursor: grab; outline: none; }
    .live:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); outline-offset: calc(-1 * var(--border-focus)); }
  `;

  @property({ attribute: false }) store: WallStore | null = null;
  @property({ attribute: false }) frame: FrameFacts | null = null;
  @property({ type: Number }) tier: Tier = 2;
  @property({ type: Boolean }) active = false;
  @property() label = '';
  @property({ attribute: false }) pose: Pose = { rot: IDENTITY_ROT, zoom: 1 };
  @state() private shown = false;
  @state() private stillUrl: string | null = null;
  @state() private live = false;

  private renderer: THREE.WebGLRenderer | null = null;
  private scene: THREE.Scene | null = null;
  private camera: THREE.PerspectiveCamera | null = null;
  private root: THREE.Group | null = null;
  private shadow: THREE.Mesh | null = null;
  /** The frame's bounds and their centre in its own coordinates (the GLB's box): the free turn pivots on the centre, not
   * on the authored origin, and the fit keeps the box's corners inside the view. */
  private bounds: THREE.Box3 | null = null;
  private centre: THREE.Vector3 | null = null;
  private open: { position: THREE.Vector3; quaternion: THREE.Quaternion } | null = null;
  private inspect: { position: THREE.Vector3; quaternion: THREE.Quaternion } | null = null;
  private progress = 0;        // 0 at the open pose, 1 at the inspect pose
  /** Where the frame is between the open pose (0) and the inspect pose (1); the tests read it. */
  get liftProgress(): number { return this.progress; }
  private raf = 0;             // the rise's (and the way back's) pending animation frame
  /** The inertia's pending frame, a handle of its own: a finger that lands cancels the inertia and never the rise's spring
   * (sharing one handle had let a touch during the rise cancel the spring's frame, and the view then stayed in `lifting`
   * with no button and Esc dead; the review of the finger change). */
  private spin = 0;
  private dirty = false;
  private pointers = new Map<number, { x: number; y: number }>();
  private pinch: { d: number; z: number } | null = null;
  private down: { x: number; y: number; t: number } | null = null;
  private last: { x: number; y: number; t: number } | null = null;
  private velocity = { x: 0, y: 0 };
  private lastTap = 0;
  private reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  private disposables: Array<{ dispose(): void }> = [];
  private ready: Promise<boolean> | null = null;
  private ro: ResizeObserver | null = null;

  override connectedCallback(): void {
    super.connectedCallback();
    const s = this.store, f = this.frame;
    if (s && f) {
      const still = s.assets.still(f.id);
      this.stillUrl = still ? s.assets.url(s.assets.file(still, 'avif') ?? s.assets.file(still)!) : null;
    }
    if (this.tier === 2) this.ready = this.setup();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.dispose();
  }

  protected override updated(changed: Map<PropertyKey, unknown>): void {
    if (changed.has('pose')) this.render3d();
  }

  // --- the scene ----------------------------------------------------------------------------------------------
  private async setup(): Promise<boolean> {
    const s = this.store, f = this.frame;
    if (!s || !f) return false;
    const glb = s.assets.glb(f.id);
    const env = s.assets.env();
    const camOpen = s.assets.camera('open');
    const camInspect = s.assets.camera('inspect');
    if (!glb || !camOpen || !camInspect) { log('lifted.no-assets', { frame: f.id, glb: !!glb, open: !!camOpen, inspect: !!camInspect }); return false; }
    const t3 = performance.now();
    const THREE = await loadThree();
    const { GLTFLoader, HDRLoader, MeshoptDecoder } = THREE;
    T = THREE;
    log('lifted.three', { ms: Math.round(performance.now() - t3) });
    await this.updateComplete;
    const canvas = this.renderRoot.querySelector('canvas') as HTMLCanvasElement | null;
    if (!canvas) return false;
    try {
      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
      renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
      renderer.toneMapping = THREE.AgXToneMapping;
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.setClearAlpha(0);          // the drawer behind shows through; the scene colour is the page's
      this.renderer = renderer;
      canvas.addEventListener('webglcontextlost', this.onContextLost, { passive: true });
    } catch (e) {
      log('lifted.webgl-failed', { error: String(e) });
      return false;
    }
    const readJson = async (e: typeof camOpen) => (await fetch(s.assets.url(s.assets.file(e)!))).json() as Promise<CameraJson>;
    const openJ = await readJson(camOpen);
    const inspectJ = await readJson(camInspect);
    const scene = new THREE.Scene();
    const c = openJ.camera.three;
    const camera = new THREE.PerspectiveCamera(c.fov_deg, 1200 / 1500, c.near, c.far);
    camera.position.fromArray(c.position);
    camera.quaternion.set(c.quaternion_xyzw[0]!, c.quaternion_xyzw[1]!, c.quaternion_xyzw[2]!, c.quaternion_xyzw[3]!);
    this.camera = camera;
    this.scene = scene;
    const poseOf = (j: CameraJson) => (j.frames?.[f.id] ?? j.frame).matrix_three;   // this frame's own pose: its bounds place it
    this.open = decompose(THREE, poseOf(openJ));
    this.inspect = decompose(THREE, poseOf(inspectJ));
    // the light: the drawer's own environment, and one warm key from the drawer's side as the scene has it
    if (env) {
      try {
        const hdr = await new HDRLoader().loadAsync(s.assets.url(s.assets.file(env)!));
        hdr.mapping = THREE.EquirectangularReflectionMapping;
        const pmrem = new THREE.PMREMGenerator(this.renderer);
        const target = pmrem.fromEquirectangular(hdr);
        scene.environment = target.texture;
        scene.environmentRotation.set(0, ENV_ROTATION_Y, 0);
        this.disposables.push(hdr, target, pmrem);
      } catch (e) {
        log('lifted.env-failed', { error: String(e) });
      }
    }
    const key = new THREE.DirectionalLight(new THREE.Color().setRGB(1.0, 0.86, 0.68, THREE.LinearSRGBColorSpace), 1.4);
    key.position.copy(this.inspect.position).add(new THREE.Vector3(0.18, 0.42, 0.3));
    key.target.position.copy(this.inspect.position);
    scene.add(key, key.target);
    // the frame
    const loader = new GLTFLoader();
    loader.setMeshoptDecoder(MeshoptDecoder);
    const t0 = performance.now();
    const gltf = await loader.loadAsync(s.assets.url(s.assets.file(glb)!)).catch((e: unknown) => { log('lifted.glb-failed', { frame: f.id, error: String(e) }); return null; });
    if (!gltf) return false;
    log('lifted.glb', { frame: f.id, ms: Math.round(performance.now() - t0) });
    const root = new THREE.Group();
    root.add(gltf.scene);
    gltf.scene.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) {
        const m = (o as THREE.Mesh).material as THREE.MeshStandardMaterial;
        if (m.name === 'lens' || m.name.startsWith('lens')) { m.transparent = true; m.depthWrite = false; }
        this.disposables.push((o as THREE.Mesh).geometry, m);
      }
    });
    // a soft contact shadow under the frame: a plane with a radial fall-off, fading as the frame rises
    const shadowTex = radialShadowTexture(THREE);
    const shadowMat = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false, opacity: 0.7 });
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const size = box.getSize(new THREE.Vector3());
    this.bounds = box;
    this.centre = box.getCenter(new THREE.Vector3());
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(size.x * 1.3, size.z * 1.6), shadowMat);
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.set((box.min.x + box.max.x) / 2, box.min.y + 0.0005, (box.min.z + box.max.z) / 2);
    root.add(shadow);
    this.shadow = shadow;
    this.disposables.push(shadow.geometry, shadowMat, shadowTex);
    scene.add(root);
    this.root = root;
    this.progress = 0;
    this.applyPose();
    this.resize();
    if ('ResizeObserver' in window && !this.ro) {
      // the host follows the viewport (a phone turned while the frame is lifted): the renderer's size follows the host
      this.ro = new ResizeObserver(() => { this.resize(); if (this.live) this.render3d(); });
      this.ro.observe(this);
    }
    this.live = true;
    this.render3d();
    return true;
  }

  private onContextLost = (ev: Event) => {
    ev.preventDefault();
    log('lifted.context-lost');
    this.live = false;
    this.dispatchEvent(new CustomEvent('tier-fallback', { detail: { reason: 'webglcontextlost' }, bubbles: true, composed: true }));
  };

  private resize(): void {
    const r = this.renderer, c = this.camera;
    if (!r || !c) return;
    const w = this.clientWidth || 1, h = this.clientHeight || 1;
    r.setSize(w, h, false);
    c.aspect = 1200 / 1500;
    c.updateProjectionMatrix();
  }

  /** The frame's transform for the current progress and pose: between the open and the inspect poses, then the free
   * turn (00-decisions.md #48), which the machine keeps in view space (the viewer's right, up and line of sight) and
   * which the camera's own rotation carries into the world, the zoom toward the camera, the pivot on the frame's centre,
   * and the fit that keeps the whole frame in the view. */
  private applyPose(): void {
    const root = this.root, o = this.open, i = this.inspect, cam = this.camera, THREE = T;
    if (!root || !o || !i || !cam || !THREE) return;
    const p = this.progress;
    const pos = o.position.clone().lerp(i.position, p);
    const q = o.quaternion.clone().slerp(i.quaternion, p);
    const [rx, ry, rz, rw] = this.pose.rot;
    const inView = new THREE.Quaternion(rx, ry, rz, rw);
    const inWorld = cam.quaternion.clone().multiply(inView).multiply(cam.quaternion.clone().invert());
    const turned = new THREE.Quaternion().slerp(inWorld, p);   // none at the open pose, the whole turn once lifted
    root.quaternion.copy(turned).multiply(q);
    // the zoom moves the frame's authored origin toward the camera along its own ray, before the pivot is added, so the
    // centre's place on the screen is the zoom's alone and the turn below never moves it (with the zoom after the pivot,
    // the centre circled as the frame turned, by 52 mm at 3x)
    const z = 1 + (clampZoom(this.pose.zoom) - 1) * p;
    const toCam = cam.position.clone().sub(pos);
    pos.add(toCam.multiplyScalar(1 - 1 / z));
    // the turn pivots on the frame's centre, so it turns in place rather than swinging about the GLB's origin: the
    // origin moves to where the turn carries it around that centre
    if (this.centre) {
      const c = this.centre.clone().applyQuaternion(q);
      pos.add(c).sub(c.clone().applyQuaternion(turned));
    }
    root.position.copy(pos);
    // the fit: a turn that would carry part of the frame past the view's edge (stood on end, the temples reach well
    // above the inspect pose's height) moves the frame back inside, along the camera's up and right, by as much as
    // there is room on the other side and no more; nothing at the inspect pose, which fits. It fades out as the zoom
    // rises (whole at 1x, gone from FIT_ZOOM_MAX), because a zoom is a choice to see a part of the frame larger than
    // the view, anchored where the fingers are, and the turn's centre must hold there. Two passes, since the corners
    // sit at different depths.
    const fit = p * Math.max(0, Math.min(1, (FIT_ZOOM_MAX - z) / (FIT_ZOOM_MAX - 1)));
    if (this.bounds && fit > 0) {
      const t = Math.tan(THREE.MathUtils.degToRad(cam.fov) / 2);
      const up = new THREE.Vector3(0, 1, 0).applyQuaternion(cam.quaternion), right = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion);
      for (let pass = 0; pass < 2; pass++) {
        const e = this.extent();
        if (!e) break;
        const dy = fitShift(e.y, t) * fit, dx = fitShift(e.x, t * cam.aspect) * fit;
        if (dy === 0 && dx === 0) break;
        root.position.add(up.clone().multiplyScalar(dy)).add(right.clone().multiplyScalar(dx));
      }
    }
    if (this.shadow) (this.shadow.material as THREE.MeshBasicMaterial).opacity = 0.7 * (1 - p);
  }

  /** The frame's box as the camera sees it: the eight corners' extent in normalised device coordinates on each axis,
   * with the depth from the camera of the corner at each end (the fit's shift is exact for that corner). */
  private extent(): { x: Extent; y: Extent } | null {
    const root = this.root, cam = this.camera, b = this.bounds, THREE = T;
    if (!root || !cam || !b || !THREE) return null;
    root.updateMatrixWorld(true);
    cam.updateMatrixWorld();   // the camera never moves, but its inverse must exist before the first draw
    const x: Extent = { min: Infinity, max: -Infinity, dMin: 0, dMax: 0 }, y: Extent = { min: Infinity, max: -Infinity, dMin: 0, dMax: 0 };
    for (let k = 0; k < 8; k++) {
      const corner = new THREE.Vector3(k & 1 ? b.max.x : b.min.x, k & 2 ? b.max.y : b.min.y, k & 4 ? b.max.z : b.min.z).applyMatrix4(root.matrixWorld);
      const d = -corner.clone().applyMatrix4(cam.matrixWorldInverse).z;
      const n = corner.project(cam);
      if (n.x < x.min) { x.min = n.x; x.dMin = d; }
      if (n.x > x.max) { x.max = n.x; x.dMax = d; }
      if (n.y < y.min) { y.min = n.y; y.dMin = d; }
      if (n.y > y.max) { y.max = n.y; y.dMax = d; }
    }
    return { x, y };
  }

  /** Where the frame is on the screen, in the host's CSS pixels: its box's extent and its centre (the tests read it). */
  screenBox(): { left: number; top: number; right: number; bottom: number; cx: number; cy: number } | null {
    const e = this.extent(), root = this.root, cam = this.camera, c = this.centre;
    if (!e || !root || !cam || !c) return null;
    const w = this.clientWidth, h = this.clientHeight;
    const n = root.localToWorld(c.clone()).project(cam);
    return { left: (e.x.min + 1) / 2 * w, right: (e.x.max + 1) / 2 * w, top: (1 - e.y.max) / 2 * h, bottom: (1 - e.y.min) / 2 * h, cx: (n.x + 1) / 2 * w, cy: (1 - n.y) / 2 * h };
  }

  private render3d(): void {
    const r = this.renderer, s = this.scene, c = this.camera;
    if (!r || !s || !c || !this.live) return;
    this.applyPose();
    r.render(s, c);
    this.dirty = false;
  }

  // --- the lift and the way back ---------------------------------------------------------------------------------
  /** The handoff and the rise; resolves when the frame rests at the inspect pose. */
  async lift(): Promise<void> {
    const ok = this.ready ? await this.ready : false;
    if (!ok && this.tier === 2) {
      // three.js, the GLB or the WebGL context failed in setup(): the still shows and the view drops to tier 1 for the
      // rest of the visit, as on a lost context, so no turn button stands over a frame that cannot turn
      this.dispatchEvent(new CustomEvent('tier-fallback', { detail: { reason: 'setup-failed' }, bubbles: true, composed: true }));
    }
    this.setShown(true);
    if (!ok || this.tier !== 2) {
      await wait(this.reduced.matches ? LIFT_REDUCED_MS : LIFT_MS);
      return;
    }
    await wait(HANDOFF_FADE_MS);
    if (this.reduced.matches) {
      this.progress = 1;
      this.render3d();
      await wait(LIFT_REDUCED_MS);
      return;
    }
    await this.animateProgress(1);
  }

  async putBack(): Promise<void> {
    if (!this.live || this.tier !== 2) {
      this.setShown(false);
      await wait(this.reduced.matches ? LIFT_REDUCED_MS : LIFT_MS);
      return;
    }
    cancelAnimationFrame(this.spin);               // an inertia still turning would hand its turns to the frame on its way back
    this.pose = { rot: IDENTITY_ROT, zoom: 1 };
    if (this.reduced.matches) {
      this.progress = 0;
      this.render3d();
      await wait(LIFT_REDUCED_MS);
    } else {
      await this.animateProgress(0);
    }
    this.setShown(false);
    await wait(HANDOFF_FADE_MS);
  }

  /** The frame's fade in or out (the still's at tier 1): the view fades the empty drawer behind it at the same moment. */
  private setShown(shown: boolean): void {
    this.shown = shown;
    this.dispatchEvent(new CustomEvent('lifted-handoff', { detail: { shown }, bubbles: true, composed: true }));
  }

  private animateProgress(target: 0 | 1): Promise<void> {
    return new Promise((resolve) => {
      let s: SpringState = { x: this.progress, v: 0 };
      let last = performance.now();
      const step = (now: number) => {
        const dt = Math.min(64, now - last);
        last = now;
        s = springStep(s, target, dt, LIFT_SPRING);
        this.progress = Math.min(1, Math.max(0, s.x));
        this.render3d();
        if (springSettled(s, target, 0.003, 0.03)) { this.progress = target; this.render3d(); resolve(); return; }
        this.raf = requestAnimationFrame(step);
      };
      this.raf = requestAnimationFrame(step);
    });
  }

  // --- the gestures: one finger turns it any way (#48), two pinch, double-tap zooms, the wheel zooms -------------
  // The view forwards every pointer event of its stage and its dim room here while the frame is rising or lifted, so the
  // finger may start anywhere on the screen but the buttons (the canvas itself binds nothing: one path, no double handling).
  // `surface` is the element that took the event, which keeps the pointer's capture; `onStage` says whether the finger is
  // over the drawer (a tap there puts the frame back; a tap on the dim room does nothing).
  pointerDown(ev: PointerEvent, surface: Element): void {
    try { surface.setPointerCapture(ev.pointerId); } catch { /* a pointer the browser no longer holds: the moves still arrive */ }
    this.pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    cancelAnimationFrame(this.spin);               // the inertia stops under the finger; the rise, if it is still on, goes on
    this.velocity = { x: 0, y: 0 };
    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      this.pinch = { d: Math.hypot(a!.x - b!.x, a!.y - b!.y), z: this.pose.zoom };
      this.down = null;
    } else if (this.active) {
      this.down = { x: ev.clientX, y: ev.clientY, t: performance.now() };
      this.last = { x: ev.clientX, y: ev.clientY, t: performance.now() };
    } else {
      // the frame is still rising: the touch is kept, never a tap, and turns the frame from the moment it rests
      this.down = null;
      this.last = null;
    }
  }

  pointerMove(ev: PointerEvent): void {
    const prev = this.pointers.get(ev.pointerId);
    if (!prev) return;
    this.pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    if (!this.active) return;                      // rising: the position is followed, the turn waits
    if (this.pinch && this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      const d = Math.hypot(a!.x - b!.x, a!.y - b!.y);
      this.dispatchEvent(new CustomEvent('lifted-zoom', { detail: { zoom: pinchZoom(this.pinch.z, d / this.pinch.d) }, bubbles: true, composed: true }));
      return;
    }
    if (this.pointers.size === 1) {
      const dx = ev.clientX - prev.x, dy = ev.clientY - prev.y;
      const now = performance.now();
      if (this.last) { const dt = Math.max(1, now - this.last.t); this.velocity = { x: 0.5 * this.velocity.x + 0.5 * dx / dt, y: 0.5 * this.velocity.y + 0.5 * dy / dt }; }
      this.last = { x: ev.clientX, y: ev.clientY, t: now };
      this.dispatchEvent(new CustomEvent('lifted-turn', { detail: { dx, dy }, bubbles: true, composed: true }));
    }
  }

  pointerUp(ev: PointerEvent, onStage: boolean): void {
    if (!this.pointers.has(ev.pointerId)) return;
    this.pointers.delete(ev.pointerId);
    if (this.pointers.size < 2) this.pinch = null;
    const d = this.down;
    this.down = null;
    if (!this.active) return;
    // a tap puts the frame back (a tap on the drawer, DRAWER-WALL.md step 7), two taps bring it closer: a finger that
    // moved as much as a small turn is a turn, never a tap (LIFTED_TAP_MAX_PX), and a tap on the dim room is nothing
    if (d && isLiftedTap(ev.clientX - d.x, ev.clientY - d.y, performance.now() - d.t)) {
      if (!onStage) return;
      const now = performance.now();
      if (now - this.lastTap < TAP_MAX_MS) {
        this.dispatchEvent(new CustomEvent('lifted-zoom', { detail: { zoom: doubleTapZoom(this.pose.zoom) }, bubbles: true, composed: true }));
        this.lastTap = 0;
      } else {
        this.lastTap = now;
        setTimeout(() => { if (this.lastTap === now) { this.lastTap = 0; this.dispatchEvent(new CustomEvent('lifted-tap', { bubbles: true, composed: true })); } }, TAP_MAX_MS);
      }
      return;
    }
    if (this.pointers.size === 0 && !this.reduced.matches) this.inertia();
  }

  private inertia(): void {
    const step = () => {
      this.velocity = { x: this.velocity.x * INERTIA_FRICTION, y: this.velocity.y * INERTIA_FRICTION };
      const dx = this.velocity.x * 16, dy = this.velocity.y * 16;
      if (Math.abs(dx) < 0.2 && Math.abs(dy) < 0.2) return;
      this.dispatchEvent(new CustomEvent('lifted-turn', { detail: { dx, dy }, bubbles: true, composed: true }));
      this.spin = requestAnimationFrame(step);
    };
    this.spin = requestAnimationFrame(step);
  }

  wheel(ev: WheelEvent): void {
    if (!this.active) return;
    ev.preventDefault();
    this.dispatchEvent(new CustomEvent('lifted-zoom', { detail: { zoom: wheelZoom(this.pose.zoom, ev.deltaY) }, bubbles: true, composed: true }));
  }

  /** Whether the live canvas has drawn anything (the tests check it drew), and how many times. */
  hasDrawn(): boolean { return this.drawCount() > 0; }
  drawCount(): number { return this.renderer?.info.render.frame ?? 0; }
  /** The WebGL renderer's name (the perf tests tell a software renderer, which presents a frame in 80 ms or more here,
   * from a GPU); null before the first setup or where the browser withholds it. */
  rendererName(): string | null {
    const gl = this.renderer?.getContext() as WebGL2RenderingContext | WebGLRenderingContext | undefined;
    const x = gl?.getExtension('WEBGL_debug_renderer_info');
    return gl && x ? String(gl.getParameter(x.UNMASKED_RENDERER_WEBGL)) : null;
  }

  private dispose(): void {
    cancelAnimationFrame(this.raf);
    cancelAnimationFrame(this.spin);
    this.ro?.disconnect();
    this.ro = null;
    for (const d of this.disposables) d.dispose();
    this.disposables = [];
    if (this.renderer) {
      this.renderer.domElement.removeEventListener('webglcontextlost', this.onContextLost);
      this.renderer.dispose();
      this.renderer.forceContextLoss();
      this.renderer = null;
    }
    this.scene = null;
    this.root = null;
    this.live = false;
  }

  override render() {
    const liveShown = this.live && this.tier === 2;
    return html`
      ${this.stillUrl && !liveShown ? html`<img class=${classMap({ still: true, fade: true, in: this.shown })} src=${this.stillUrl} alt=${this.label} draggable="false">` : nothing}
      <canvas class=${classMap({ live: true, fade: true, in: this.shown && liveShown })} role="img" aria-label=${this.label} tabindex=${this.active ? 0 : -1}></canvas>
    `;
  }
}

interface Extent { min: number; max: number; dMin: number; dMax: number }

/** The fit's shift along one axis of the view, in world metres: the amount past the edge (in normalised device
 * coordinates, the view ±1) times the depth of the corner that is past it times the camera's half-angle tangent, which
 * is exactly the move that brings that corner to the edge, limited to the room on the other side, measured the same
 * way for the corner there; nothing when both ends are past the edges (zoomed in) or neither is. */
function fitShift(e: Extent, t: number): number {
  const over = e.max - 1, under = -1 - e.min;
  if (over > 0 && under <= 0) return -Math.min(over * e.dMax, -under * e.dMin) * t;
  if (under > 0 && over <= 0) return Math.min(under * e.dMin, -over * e.dMax) * t;
  return 0;
}

function decompose(THREE: ThreeModule, m: number[][]): { position: THREE.Vector3; quaternion: THREE.Quaternion } {
  const mat = new THREE.Matrix4().set(m[0]![0]!, m[0]![1]!, m[0]![2]!, m[0]![3]!, m[1]![0]!, m[1]![1]!, m[1]![2]!, m[1]![3]!, m[2]![0]!, m[2]![1]!, m[2]![2]!, m[2]![3]!, m[3]![0]!, m[3]![1]!, m[3]![2]!, m[3]![3]!);
  const position = new THREE.Vector3(), quaternion = new THREE.Quaternion(), scale = new THREE.Vector3();
  mat.decompose(position, quaternion, scale);
  return { position, quaternion };
}

function radialShadowTexture(THREE: ThreeModule): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const ctx = c.getContext('2d')!;
  const g = ctx.createRadialGradient(64, 64, 8, 64, 64, 64);
  const dark = getComputedStyle(document.documentElement).getPropertyValue('--color-surface-scene').trim() || 'transparent';
  g.addColorStop(0, dark);
  g.addColorStop(1, 'transparent');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const wait = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

declare global { interface HTMLElementTagNameMap { 'lifted-frame': LiftedFrame } }
