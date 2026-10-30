import type {Meta, StoryObj} from '@storybook/react-vite';
import {Entry} from '~/components/house/Entry';
import {FramesPage} from '~/components/pages/FramesPage';
import {ListOffer} from '~/components/house/ListOffer';
import {MenuSheet} from '~/components/house/MenuSheet';
import {SensoryNotice} from '~/components/house/SensoryNotice';
import {drops, fullBag, Page, products} from './fixtures';

/** The layers a page can carry: the menu sheet, the bag drawer, the list pop-up, the photosensitivity notice, the entry. */
const meta = {
  title: 'Pages/Overlays',
  parameters: {layout: 'fullscreen'},
} satisfies Meta;
export default meta;
type Story = StoryObj<typeof meta>;

export const MenuOpen: Story = {
  name: 'Menu sheet · open',
  render: () => (
    <Page>
      <FramesPage products={products} drop={drops.announcedNoDate} />
      <MenuSheet open onClose={() => undefined} drop={drops.announcedNoDate} />
    </Page>
  ),
};
export const BagDrawerOpen: Story = {
  name: 'Bag drawer · open, two lines',
  render: () => (
    <Page bag={fullBag} bagOpen drop={drops.live}>
      <FramesPage products={products} drop={drops.live} />
    </Page>
  ),
};
export const BagDrawerEmpty: Story = {
  name: 'Bag drawer · open, empty',
  render: () => (
    <Page bagOpen>
      <FramesPage products={products} drop={drops.announcedNoDate} />
    </Page>
  ),
};
export const ListPopUp: Story = {
  name: 'List pop-up · open',
  render: () => (
    <Page>
      <FramesPage products={products} drop={drops.announcedNoDate} />
      <ListOffer open onClose={() => undefined} />
    </Page>
  ),
};
export const PhotosensitivityNotice: Story = {
  name: 'Photosensitivity notice',
  render: () => (
    <Page>
      <FramesPage products={products} drop={drops.announcedNoDate} />
      <SensoryNotice onContinue={() => undefined} onSkip={() => undefined} />
    </Page>
  ),
};
export const EntryFrameList: Story = {
  name: 'Entry · as a frame list (wire)',
  render: () => (
    <Page>
      <main id="main">
        <Entry wire onDone={() => undefined} />
      </main>
    </Page>
  ),
};
