// three.js for <lifted-frame>, gathered here as named re-exports: <lifted-frame> imports this module dynamically at a
// tier-2 lift, so the library is loaded only then (never in the initial bundle, never at tier 1), and because the
// imports are named, the bundler keeps only what the live frame uses. A dynamic import('three') itself would carry
// the whole library (its namespace object cannot be tree-shaken: 819 kB against 647 kB).
export {
  WebGLRenderer, Scene, PerspectiveCamera, DirectionalLight, Color, Vector3, Quaternion, Group, Mesh, MeshBasicMaterial,
  Box3, PlaneGeometry, Matrix4, CanvasTexture, PMREMGenerator, MathUtils,
  AgXToneMapping, SRGBColorSpace, LinearSRGBColorSpace, EquirectangularReflectionMapping,
} from 'three';
export { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
export { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
export { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
