import {RouterContextProvider} from 'react-router';
import {createStore, store, type Store} from '~/lib/mock';
import {settingsFrom, type SiteSettings} from '~/lib/settings';

/** What every loader and action gets as `context`. No Shopify clients in this phase (RUN.md, phase 0). */
export interface DsLoadContext {
  env: Env;
  waitUntil: (promise: Promise<unknown>) => void;
  /** Local data in Storefront API shape; the live client replaces it at launch. */
  store: Store;
  settings: SiteSettings;
  /** The request's clock, so drop states and countdowns are computed once per request. */
  now: Date;
}

export function createDsContext(
  request: Request,
  env: Env,
  executionContext: ExecutionContext,
): RouterContextProvider & DsLoadContext {
  const now = new Date();
  // Drop state depends on the clock; rebuild the store only when a drop carries a time.
  const timed = store.drops.all().some((d) => d.startsAt || d.endsAt);
  const context = new RouterContextProvider() as RouterContextProvider & DsLoadContext;
  Object.assign(context, {
    env,
    waitUntil: executionContext.waitUntil.bind(executionContext),
    store: timed ? createStore(now) : store,
    settings: settingsFrom(env),
    now,
  } satisfies DsLoadContext);
  return context;
}
