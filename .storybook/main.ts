import type {StorybookConfig} from '@storybook/react-vite';

/**
 * Storybook for the Darkest Shades components (docs/brief/05-components.md): a story per state. Size
 * (390, 1440) and mode (UI, wire) are globals, so every story renders in all four combinations; the
 * Playwright matrix in tests/e2e/storybook.spec.ts screenshots and axe-checks each one.
 */
const config: StorybookConfig = {
  stories: ['../app/**/*.stories.@(ts|tsx)'],
  addons: ['@storybook/addon-a11y'],
  framework: {name: '@storybook/react-vite', options: {}},
  core: {
    disableTelemetry: true,
    disableWhatsNewNotifications: true,
    builder: {name: '@storybook/builder-vite', options: {viteConfigPath: '.storybook/vite.config.ts'}},
  },
  staticDirs: [
    {from: '../assets/photography', to: '/photography'},
    {from: '../assets/entry', to: '/entry'},
  ],
};

export default config;
