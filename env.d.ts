/// <reference types="vite/client" />
/// <reference types="react-router" />
/// <reference types="@shopify/oxygen-workers-types" />

// Enhance TypeScript's built-in typings.
import '@total-typescript/ts-reset';
import type {DsLoadContext} from '~/lib/context';

declare global {
  /** Environment variables (MiniOxygen in dev, Oxygen at launch). Nothing Shopify in this phase: .env.example. */
  interface Env {
    DS_REVIEW_BUILD?: string;
    PUBLIC_ADOBE_FONTS_KIT?: string;
    PUBLIC_PAIRS_LEFT_THRESHOLD?: string;
    SESSION_SECRET?: string;
  }

  interface ImportMetaEnv {
    readonly DS_REVIEW_BUILD?: string;
    readonly DS_LOCAL_FONTS?: string;
  }
}

declare module 'react-router' {
  interface RouterContextProvider extends DsLoadContext {}
  interface AppLoadContext extends DsLoadContext {}
}
