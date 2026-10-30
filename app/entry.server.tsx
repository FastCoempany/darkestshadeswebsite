import {ServerRouter, type EntryContext, type RouterContextProvider} from 'react-router';
import {isbot} from 'isbot';
import {renderToReadableStream} from 'react-dom/server';
import {createContentSecurityPolicy} from '@shopify/hydrogen';

export default async function handleRequest(
  request: Request,
  responseStatusCode: number,
  responseHeaders: Headers,
  reactRouterContext: EntryContext,
  context: RouterContextProvider,
) {
  // Fonts come from the app itself (the stand-ins) or, with a kit id set, from Adobe Fonts (route A in
  // brand/fonts/README.md). Those are the only third-party hosts the policy ever names.
  const kit = context.settings.adobeFontsKit;
  const kitHosts = kit ? ['https://use.typekit.net', 'https://p.typekit.net'] : [];
  const {nonce, header, NonceProvider} = createContentSecurityPolicy({
    styleSrc: ["'self'", "'unsafe-inline'", ...kitHosts],
    fontSrc: ["'self'", 'data:', ...kitHosts],
    imgSrc: ["'self'", 'data:', ...(kit ? ['https://p.typekit.net'] : [])],
    connectSrc: ["'self'", ...kitHosts],
  });

  const body = await renderToReadableStream(
    <NonceProvider>
      <ServerRouter context={reactRouterContext} url={request.url} nonce={nonce} />
    </NonceProvider>,
    {
      nonce,
      signal: request.signal,
      onError(error) {
        console.error(error);
        responseStatusCode = 500;
      },
    },
  );

  if (isbot(request.headers.get('user-agent'))) {
    await body.allReady;
  }

  responseHeaders.set('Content-Type', 'text/html');
  responseHeaders.set('Content-Security-Policy', header);

  return new Response(body, {
    headers: responseHeaders,
    status: responseStatusCode,
  });
}
