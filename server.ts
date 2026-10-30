import * as serverBuild from 'virtual:react-router/server-build';
import {createRequestHandler} from 'react-router';
import {createDsContext} from '~/lib/context';

/**
 * The worker's fetch handler (MiniOxygen in dev, Oxygen at launch).
 *
 * This phase runs React Router's request handler with a Shopify-free context: no Storefront, cart or
 * customer-account client, no storefrontRedirect (docs/build/RUN.md, phase 0). At launch,
 * `createHydrogenContext` and Hydrogen's `createRequestHandler` take their places here.
 */
export default {
  async fetch(request: Request, env: Env, executionContext: ExecutionContext): Promise<Response> {
    try {
      const context = createDsContext(request, env, executionContext);
      const handleRequest = createRequestHandler(serverBuild, process.env.NODE_ENV);
      return await handleRequest(request, context);
    } catch (error) {
      console.error(error);
      return new Response('An unexpected error occurred', {status: 500});
    }
  },
};
