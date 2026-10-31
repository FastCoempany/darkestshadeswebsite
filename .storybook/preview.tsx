import type {Decorator, Preview} from '@storybook/react-vite';
import {useEffect} from 'react';
import {createMemoryRouter, RouterProvider} from 'react-router';
import '../app/styles/tailwind.css';
import '@fontsource-variable/mona-sans/standard.css';
import '@fontsource-variable/urbanist/index.css';

/** Mode and theme live on <html>, as in the app: data-mode="wire" for wireframes, data-theme for night or paper. */
// Stories are still: no clocks tick and no scroll-driven state changes (countdowns, the scale cut).
if (typeof window !== 'undefined') (window as Window & {__dsStatic?: boolean}).__dsStatic = true;

function applyModeAndTheme(mode?: string, theme?: string) {
  const html = document.documentElement;
  if (mode === 'wire') html.dataset.mode = 'wire';
  else delete html.dataset.mode;
  html.dataset.theme = theme === 'paper' ? 'paper' : 'night';
}

function ModeAndTheme({mode, theme, children}: {mode?: string; theme?: string; children: React.ReactNode}) {
  // Before the story renders, so components that read the mode on mount see it; again after, for changes.
  applyModeAndTheme(mode, theme);
  useEffect(() => applyModeAndTheme(mode, theme), [mode, theme]);
  return <>{children}</>;
}

/** A data router per story: pages use <Link>, <Form> and route hooks the way they do in the app. */
function StoryRouter({children}: {children: React.ReactNode}) {
  const router = createMemoryRouter([{path: '*', element: children, action: () => null}], {initialEntries: ['/']});
  return <RouterProvider router={router} />;
}

const withModeAndTheme: Decorator = (Story, context) => (
  <ModeAndTheme mode={context.globals.mode as string | undefined} theme={context.globals.theme as string | undefined}>
    <StoryRouter>
      <Story />
    </StoryRouter>
  </ModeAndTheme>
);

const preview: Preview = {
  decorators: [withModeAndTheme],
  globalTypes: {
    mode: {
      description: 'UI or wireframe rendering',
      toolbar: {title: 'Mode', icon: 'contrast', items: [{value: 'ui', title: 'UI'}, {value: 'wire', title: 'Wire'}], dynamicTitle: true},
    },
    theme: {
      description: 'Night (default) or paper',
      toolbar: {title: 'Theme', icon: 'paintbrush', items: [{value: 'night', title: 'Night'}, {value: 'paper', title: 'Paper'}], dynamicTitle: true},
    },
  },
  initialGlobals: {mode: 'ui', theme: 'night', viewport: {value: 'phone390', isRotated: false}},
  parameters: {
    layout: 'fullscreen',
    backgrounds: {disable: true},
    viewport: {
      options: {
        phone320: {name: 'Phone 320', styles: {width: '320px', height: '568px'}, type: 'mobile'},
        phone390: {name: 'Phone 390', styles: {width: '390px', height: '844px'}, type: 'mobile'},
        tablet768: {name: 'Tablet 768', styles: {width: '768px', height: '1024px'}, type: 'tablet'},
        laptop1024: {name: 'Laptop 1024', styles: {width: '1024px', height: '768px'}, type: 'desktop'},
        desktop1440: {name: 'Desktop 1440', styles: {width: '1440px', height: '900px'}, type: 'desktop'},
      },
    },
    a11y: {test: 'error'},
    controls: {expanded: true},
  },
};

export default preview;
