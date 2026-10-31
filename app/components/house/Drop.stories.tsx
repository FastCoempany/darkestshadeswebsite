import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {drops, STORY_NOW} from '~/components/pages/stories/fixtures';
import {Countdown} from './Countdown';
import {DropLine} from './DropLine';
import {DropStatus} from './DropStatus';
import {LookNumber} from './LookNumber';
import {PairsLeft} from './PairsLeft';

/** Honesty in code: every one of these renders nothing for a missing value (05, Behavior rules). */
const meta = {
  title: 'House/Drop',
  parameters: {layout: 'padded'},
  decorators: [(Story) => <div className="grid max-w-xl gap-6"><Story /></div>],
} satisfies Meta;
export default meta;
type Story = StoryObj<typeof meta>;

export const StatusAnnouncedNoDate: Story = {name: 'DropStatus · announced, no date (today)', render: () => <DropStatus drop={drops.announcedNoDate} />};
export const StatusAnnounced: Story = {name: 'DropStatus · announced with a date', render: () => <DropStatus drop={drops.announcedWithDate} />};
export const StatusLive: Story = {name: 'DropStatus · live', render: () => <DropStatus drop={drops.live} />};
export const StatusSoldOut: Story = {name: 'DropStatus · sold out', render: () => <DropStatus drop={drops.soldOut} />};
export const StatusEnded: Story = {name: 'DropStatus · ended', render: () => <DropStatus drop={drops.ended} />};
export const StatusNone: Story = {name: 'DropStatus · none (renders nothing)', render: () => <DropStatus drop={null} />};
export const StatusSmall: Story = {name: 'DropStatus · small (home)', render: () => <DropStatus drop={drops.announcedWithDate} variant="small" />};

export const LineAnnouncedNoDate: Story = {name: 'DropLine · announced, no date', render: () => <DropLine drop={drops.announcedNoDate} />};
export const LineAnnounced: Story = {name: 'DropLine · announced with a date', render: () => <DropLine drop={drops.announcedWithDate} />};
export const LineLive: Story = {name: 'DropLine · live, real numbers', render: () => <DropLine drop={drops.live} />};
export const LineHidden: Story = {name: 'DropLine · hidden (no drop, ended, sold out)', render: () => <><DropLine drop={null} /><DropLine drop={drops.ended} /><DropLine drop={drops.soldOut} /></>};

export const CountdownRunning: Story = {name: 'Countdown · running', render: () => <Countdown to={drops.announcedWithDate.startsAt} now={STORY_NOW.toISOString()} label={copy.drop.countdownLabel.toStart} />};
export const CountdownReached: Story = {name: 'Countdown · reached (renders nothing)', render: () => <Countdown to="2027-02-01T00:00:00Z" now={STORY_NOW.toISOString()} label={copy.drop.countdownLabel.toStart} />};
export const CountdownNoTime: Story = {name: 'Countdown · no time (renders nothing)', render: () => <Countdown to={null} now={STORY_NOW.toISOString()} label={copy.drop.countdownLabel.toStart} />};

export const PairsFew: Story = {name: 'PairsLeft · few', render: () => <PairsLeft left={3} total={15} />};
export const PairsMany: Story = {name: 'PairsLeft · many, above the threshold (hidden)', render: () => <PairsLeft left={37} total={120} threshold={20} />};
export const PairsNone: Story = {name: 'PairsLeft · none (no inventory, renders nothing)', render: () => <PairsLeft left={null} />};

export const Look: Story = {name: 'LookNumber', render: () => <div className="flex gap-4"><LookNumber number="01" /><LookNumber number="08" /><LookNumber number="09" /></div>};
