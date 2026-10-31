import type {Meta, StoryObj} from '@storybook/react-vite';
import {AccessibilityPage} from '~/components/pages/AccessibilityPage';
import {AccountPage} from '~/components/pages/AccountPage';
import {BagPage} from '~/components/pages/BagPage';
import {CarePage} from '~/components/pages/CarePage';
import {CastPage} from '~/components/pages/CastPage';
import {DropPage} from '~/components/pages/DropPage';
import {FramePage} from '~/components/pages/FramePage';
import {FramesPage} from '~/components/pages/FramesPage';
import {HomePage} from '~/components/pages/HomePage';
import {ManifestoPage} from '~/components/pages/ManifestoPage';
import {NotFoundPage} from '~/components/pages/NotFoundPage';
import {PoliciesIndexPage, PolicyPage} from '~/components/pages/PolicyPage';
import {QuestionsPage} from '~/components/pages/QuestionsPage';
import gcdRender from '../../../../brand/emblems/gcd/render/gcd-3d-yaw35-1024.png?url';
import {store} from '~/lib/mock';
import {cast, drops, fullBag, Page, products} from './fixtures';

/**
 * Every template in 04-ia-and-pages.md, in every state a page can be in. The drop states that today's
 * data does not have (a date, live, sold out, ended) come from fixtures, never from a route.
 */
const meta = {
  title: 'Pages/Templates',
  parameters: {layout: 'fullscreen'},
} satisfies Meta;
export default meta;
type Story = StoryObj<typeof meta>;

const f01 = products[0];
const f08 = products.find((p) => p.ds.id === 'F08')!;

export const Home: Story = {
  render: () => (
    <Page headerSurface="transparent" footerList={false}>
      <HomePage products={products} drop={drops.announcedNoDate} cast={cast} detail={store.images.forShot('F09', 'A6')} dropHero={store.images.forShot('F09', 'H')} />
    </Page>
  ),
};

export const HomeAfterTheCut: Story = {
  name: 'Home · the drop after its cut',
  render: () => (
    <Page headerSurface="transparent" footerList={false}>
      <HomePage products={products} drop={drops.announcedNoDate} cast={cast} detail={store.images.forShot('F09', 'A6')} dropHero={store.images.forShot('F09', 'H')} cut />
    </Page>
  ),
};

export const HomeLive: Story = {
  name: 'Home · the drop live, after its cut',
  render: () => (
    <Page headerSurface="transparent" footerList={false} drop={drops.live}>
      <HomePage products={products} drop={drops.live} cast={cast} detail={store.images.forShot('F09', 'A6')} dropHero={store.images.forShot('F09', 'H')} cut />
    </Page>
  ),
};
export const HomeSoldOut: Story = {
  name: 'Home · the drop sold out, after its cut',
  render: () => (
    <Page headerSurface="transparent" footerList={false} drop={drops.soldOut}>
      <HomePage products={products} drop={drops.soldOut} cast={cast} detail={store.images.forShot('F09', 'A6')} dropHero={store.images.forShot('F09', 'H')} cut />
    </Page>
  ),
};
export const HomeEnded: Story = {
  name: 'Home · the drop ended, after its cut',
  render: () => (
    <Page headerSurface="transparent" footerList={false} drop={drops.ended}>
      <HomePage products={products} drop={drops.ended} cast={cast} detail={store.images.forShot('F09', 'A6')} dropHero={store.images.forShot('F09', 'H')} cut />
    </Page>
  ),
};

export const DropAnnouncedNoDate: Story = {
  name: 'Drop · announced, no date (today)',
  render: () => (
    <Page drop={drops.announcedNoDate} footerList={false} dropLine={false}>
      <DropPage drop={drops.announcedNoDate} products={products} />
    </Page>
  ),
};
export const DropAnnouncedWithDate: Story = {
  name: 'Drop · announced with a date',
  render: () => (
    <Page drop={drops.announcedWithDate} footerList={false} dropLine={false}>
      <DropPage drop={drops.announcedWithDate} products={products} />
    </Page>
  ),
};
export const DropLive: Story = {
  name: 'Drop · live',
  render: () => (
    <Page drop={drops.live} footerList={false} dropLine={false}>
      <DropPage drop={drops.live} products={products} />
    </Page>
  ),
};
export const DropSoldOut: Story = {
  name: 'Drop · sold out',
  render: () => (
    <Page drop={drops.soldOut} footerList={false} dropLine={false}>
      <DropPage drop={drops.soldOut} products={products} />
    </Page>
  ),
};
export const DropEnded: Story = {
  name: 'Drop · ended',
  render: () => (
    <Page drop={drops.ended} footerList={false} dropLine={false}>
      <DropPage drop={drops.ended} products={products} />
    </Page>
  ),
};
export const DropWithArchive: Story = {
  name: 'Drop · announced, with a past drop in the archive',
  render: () => (
    <Page drop={drops.announcedWithDate} footerList={false} dropLine={false}>
      <DropPage drop={{...drops.announcedWithDate, number: '002'}} products={products} others={[{number: '001', state: 'ended'}]} />
    </Page>
  ),
};

export const Frames: Story = {
  render: () => (
    <Page>
      <FramesPage products={products} drop={drops.announcedNoDate} />
    </Page>
  ),
};
export const FramesLive: Story = {
  name: 'Frames · drop live',
  render: () => (
    <Page drop={drops.live}>
      <FramesPage products={products} drop={drops.live} />
    </Page>
  ),
};

export const Frame: Story = {
  name: 'Frame · F01',
  render: () => (
    <Page>
      <FramePage product={f01} drop={drops.announcedNoDate} castShots={store.cast.shotsForFrame('F01')} next={store.products.next('F01')} />
    </Page>
  ),
};
export const FrameLive: Story = {
  name: 'Frame · F01, drop live',
  render: () => (
    <Page drop={drops.live}>
      <FramePage product={f01} drop={drops.live} castShots={store.cast.shotsForFrame('F01')} next={store.products.next('F01')} />
    </Page>
  ),
};
export const FrameSoldOut: Story = {
  name: 'Frame · F01, sold out',
  render: () => (
    <Page drop={drops.soldOut}>
      <FramePage product={f01} drop={drops.soldOut} castShots={store.cast.shotsForFrame('F01')} next={store.products.next('F01')} />
    </Page>
  ),
};
export const FrameEnded: Story = {
  name: 'Frame · F01, drop ended (the next drop line)',
  render: () => (
    <Page drop={drops.ended}>
      <FramePage product={f01} drop={drops.ended} castShots={store.cast.shotsForFrame('F01')} next={store.products.next('F01')} />
    </Page>
  ),
};
export const FrameNoDrop: Story = {
  name: 'Frame · F01, no drop',
  render: () => (
    <Page drop={null}>
      <FramePage product={f01} drop={null} castShots={store.cast.shotsForFrame('F01')} next={store.products.next('F01')} />
    </Page>
  ),
};
export const FramesSoldOut: Story = {
  name: 'Frames · drop sold out',
  render: () => (
    <Page drop={drops.soldOut}>
      <FramesPage products={products} drop={drops.soldOut} />
    </Page>
  ),
};
export const FramesEnded: Story = {
  name: 'Frames · drop ended (the next drop word)',
  render: () => (
    <Page drop={drops.ended}>
      <FramesPage products={products} drop={drops.ended} />
    </Page>
  ),
};
export const FramesNoDrop: Story = {
  name: 'Frames · no drop',
  render: () => (
    <Page drop={null}>
      <FramesPage products={products} drop={null} />
    </Page>
  ),
};
export const FrameF08: Story = {
  name: 'Frame · F08 (the GCD render in the detail hold)',
  render: () => (
    <Page>
      <FramePage product={f08} drop={drops.announcedNoDate} castShots={store.cast.shotsForFrame('F08')} next={store.products.next('F08')} detailRender={gcdRender} />
    </Page>
  ),
};

export const Manifesto: Story = {
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <ManifestoPage />
    </Page>
  ),
};
export const Cast: Story = {
  render: () => (
    <Page>
      <CastPage members={cast} products={products} />
    </Page>
  ),
};
export const Questions: Story = {
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <QuestionsPage />
    </Page>
  ),
};
export const Care: Story = {
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <CarePage />
    </Page>
  ),
};
export const Policies: Story = {
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <PoliciesIndexPage />
    </Page>
  ),
};
export const PolicyExchange: Story = {
  name: 'Policy · exchange',
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <PolicyPage handle="exchange" />
    </Page>
  ),
};
export const PolicyWarranty: Story = {
  name: 'Policy · warranty',
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <PolicyPage handle="warranty" />
    </Page>
  ),
};
export const PolicyPrivacy: Story = {
  name: 'Policy · privacy (no settled promise: the title and the pending line)',
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <PolicyPage handle="privacy" />
    </Page>
  ),
};
export const Accessibility: Story = {
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <AccessibilityPage introOn />
    </Page>
  ),
};
export const AccessibilityIntroOff: Story = {
  name: 'Accessibility · intro off, saved',
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <AccessibilityPage introOn={false} saved />
    </Page>
  ),
};
export const NotFound: Story = {
  name: '404',
  render: () => (
    <Page>
      <NotFoundPage />
    </Page>
  ),
};
export const ServerError: Story = {
  name: '500 (any failure)',
  render: () => (
    <Page>
      <NotFoundPage status={500} />
    </Page>
  ),
};
export const Account: Story = {
  globals: {theme: 'paper'},
  render: () => (
    <Page>
      <AccountPage />
    </Page>
  ),
};
export const BagEmpty: Story = {
  name: 'Bag · empty',
  render: () => (
    <Page>
      <BagPage />
    </Page>
  ),
};
export const BagFull: Story = {
  name: 'Bag · two lines',
  render: () => (
    <Page bag={fullBag} drop={drops.live}>
      <BagPage limit={2} />
    </Page>
  ),
};
