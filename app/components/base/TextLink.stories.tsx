import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy, instagramUrl} from '~/lib/copy';
import {TextLink} from './TextLink';

function Sheet({force}: {force?: 'hover' | 'focus-visible'}) {
  return (
    <div className="grid gap-6 p-6">
      <p className="font-text text-body text-ds-text-primary">
        {copy.questions.items[4].a.split('.')[0]}. <TextLink to="/frames" data-force={force}>{copy.nav.frames}</TextLink>.
      </p>
      <nav className="flex gap-6">
        <TextLink to="/drop" variant="nav" activePrefix="/drop" data-force={force}>{copy.nav.drop}</TextLink>
        <TextLink to="/" variant="nav" data-force={force}>{copy.nav.frames}</TextLink>
        <TextLink to="/manifesto" variant="nav" data-force={force}>{copy.nav.manifesto}</TextLink>
      </nav>
      <ul className="grid gap-2">
        <li><TextLink to="/questions" variant="footer" data-force={force}>{copy.footer.links.questions}</TextLink></li>
        <li><TextLink to={instagramUrl()} variant="footer" external>{copy.meta.instagram}</TextLink></li>
      </ul>
    </div>
  );
}

const meta = {title: 'Base/TextLink', component: TextLink, parameters: {layout: 'fullscreen'}, args: {to: '/frames', children: copy.nav.frames}} satisfies Meta<typeof TextLink>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {render: () => <Sheet />};
export const Hover: Story = {render: () => <Sheet force="hover" />};
export const FocusVisible: Story = {render: () => <Sheet force="focus-visible" />};
