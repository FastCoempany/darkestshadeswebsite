// <lifted-frame> (DRAWER-WALL.md, steps 4 and 5, In the browser): the live 3D frame, three.js inside, loaded on the
// first open and never in the initial bundle. One canvas, rendered only while something changes, AgX tone mapping,
// the drawer's own HDR as the environment plus one warm key matched to the scene. The handoff: the canvas mounts
// over the drawer's last frame with the GLB at open.json's transform and a soft contact shadow, cross-fades over
// 120 ms, then springs to the inspect pose; turning, pinching and the wheel report deltas up to the view, whose
// machine holds the pose. Tier 1 shows the lifted still instead. On a lost context: tier 1 for the rest of the visit.
import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { classMap } from 'lit/directives/class-map.js';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import type { WallStore } from '../data/store';
import type { FrameFacts } from '../lib/types';
import type { Tier } from '../lib/tier';
import { HANDOFF_FADE_MS, INERTIA_FRICTION, LIFT_MS, LIFT_REDUCED_MS, PITCH_PER_PX, YAW_PER_PX, clampZoom, isTap, pinchZoom, doubleTapZoom, wheelZoom, TAP_MAX_MS } from '../lib/gestures';
import { springStep, springSettled, type SpringState } from '../lib/spring';
import { log } from '../lib/log';

export interface Pose { yaw: number; pitch: number; zoom: number }
interface FramePose { matrix_three: number[][] }
// camera/open.json and inspect.json: the camera, every frame's pose under `frames` (the default frame's again as `frame`)
interface CameraJson { camera: { three: { position: number[]; fov_deg: number; near: number; far: number; quaternion_xyzw: number[] } }; frame: FramePose; frames?: Record<string, FramePose> }

const LIFT_SPRING = { stiffness: 120, damping: 20 };
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
  @property({ attribute: false }) pose: Pose = { yaw: 0, pitch: 0, zoom: 1 };
  @state() private shown = false;
  @state() private stillUrl: string | null = null;
  @state() private live = false;

  private renderer: THREE.WebGLRenderer | null = null;
  private scene: THREE.Scene | null = null;
  private camera: THREE.PerspectiveCamera | null = null;
  private root: THREE.Group | null = null;
  private shadow: THREE.Mesh | null = null;
  private open: { position: THREE.Vector3; quaternion: THREE.Quaternion } | null = null;
  private inspect: { position: THREE.Vector3; quaternion: THREE.Quaternion } | null = null;
  private progress = 0;        // 0 at the open pose, 1 at the inspect pose
  private raf = 0;
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
    this.open = decompose(poseOf(openJ));
    this.inspect = decompose(poseOf(inspectJ));
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
    let gltf: Awaited<ReturnType<GLTFLoader['loadAsync']>>;
    try {
      gltf = await loader.loadAsync(s.assets.url(s.assets.file(glb)!));
    } catch (e) {
      log('lifted.glb-failed', { frame: f.id, error: String(e) });
      return false;
    }
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
    const shadowTex = radialShadowTexture();
    const shadowMat = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false, opacity: 0.7 });
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const size = box.getSize(new THREE.Vector3());
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

  /** The frame's transform for the current progress and pose: between the open and the inspect poses, then yaw
   * about its own vertical, pitch about the camera's right, and zoom toward the camera. */
  private applyPose(): void {
    const root = this.root, o = this.open, i = this.inspect, cam = this.camera;
    if (!root || !o || !i || !cam) return;
    const p = this.progress;
    const pos = o.position.clone().lerp(i.position, p);
    const q = o.quaternion.clone().slerp(i.quaternion, p);
    const yaw = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(this.pose.yaw) * p);
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(cam.quaternion);
    const pitch = new THREE.Quaternion().setFromAxisAngle(right, THREE.MathUtils.degToRad(this.pose.pitch) * p);
    root.quaternion.copy(pitch).multiply(yaw).multiply(q);
    const z = 1 + (clampZoom(this.pose.zoom) - 1) * p;
    const toCam = cam.position.clone().sub(pos);
    pos.add(toCam.multiplyScalar(1 - 1 / z));
    root.position.copy(pos);
    if (this.shadow) (this.shadow.material as THREE.MeshBasicMaterial).opacity = 0.7 * (1 - p);
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
    this.shown = true;
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
      this.shown = false;
      await wait(this.reduced.matches ? LIFT_REDUCED_MS : LIFT_MS);
      return;
    }
    this.pose = { yaw: 0, pitch: 0, zoom: 1 };
    if (this.reduced.matches) {
      this.progress = 0;
      this.render3d();
      await wait(LIFT_REDUCED_MS);
    } else {
      await this.animateProgress(0);
    }
    this.shown = false;
    await wait(HANDOFF_FADE_MS);
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

  // --- the gestures: one finger turns, two pinch, double-tap zooms, the wheel zooms -----------------------------
  private onPointerDown(ev: PointerEvent): void {
    if (!this.active) return;
    (ev.currentTarget as HTMLElement).setPointerCapture(ev.pointerId);
    this.pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    cancelAnimationFrame(this.raf);
    this.velocity = { x: 0, y: 0 };
    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      this.pinch = { d: Math.hypot(a!.x - b!.x, a!.y - b!.y), z: this.pose.zoom };
      this.down = null;
    } else {
      this.down = { x: ev.clientX, y: ev.clientY, t: performance.now() };
      this.last = { x: ev.clientX, y: ev.clientY, t: performance.now() };
    }
  }

  private onPointerMove(ev: PointerEvent): void {
    const prev = this.pointers.get(ev.pointerId);
    if (!prev || !this.active) return;
    this.pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
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

  private onPointerUp(ev: PointerEvent): void {
    this.pointers.delete(ev.pointerId);
    if (this.pointers.size < 2) this.pinch = null;
    const d = this.down;
    this.down = null;
    if (d && isTap(ev.clientX - d.x, ev.clientY - d.y, performance.now() - d.t)) {
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
      this.raf = requestAnimationFrame(step);
    };
    this.raf = requestAnimationFrame(step);
  }

  private onWheel(ev: WheelEvent): void {
    if (!this.active) return;
    ev.preventDefault();
    this.dispatchEvent(new CustomEvent('lifted-zoom', { detail: { zoom: wheelZoom(this.pose.zoom, ev.deltaY) }, bubbles: true, composed: true }));
  }

  /** Whether the live canvas has drawn anything (the tests check it drew). */
  hasDrawn(): boolean {
    const r = this.renderer;
    return !!r && r.info.render.frame > 0;
  }

  private dispose(): void {
    cancelAnimationFrame(this.raf);
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
      <canvas class=${classMap({ live: true, fade: true, in: this.shown && liveShown })} role="img" aria-label=${this.label} tabindex=${this.active ? 0 : -1}
        @pointerdown=${this.onPointerDown} @pointermove=${this.onPointerMove} @pointerup=${this.onPointerUp} @pointercancel=${this.onPointerUp} @wheel=${this.onWheel}></canvas>
    `;
  }
}

function decompose(m: number[][]): { position: THREE.Vector3; quaternion: THREE.Quaternion } {
  const mat = new THREE.Matrix4().set(m[0]![0]!, m[0]![1]!, m[0]![2]!, m[0]![3]!, m[1]![0]!, m[1]![1]!, m[1]![2]!, m[1]![3]!, m[2]![0]!, m[2]![1]!, m[2]![2]!, m[2]![3]!, m[3]![0]!, m[3]![1]!, m[3]![2]!, m[3]![3]!);
  const position = new THREE.Vector3(), quaternion = new THREE.Quaternion(), scale = new THREE.Vector3();
  mat.decompose(position, quaternion, scale);
  return { position, quaternion };
}

function radialShadowTexture(): THREE.CanvasTexture {
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
