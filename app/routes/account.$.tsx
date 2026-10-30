import type {Route} from './+types/account.$';
import {AccountPage} from '~/components/pages/AccountPage';
import {copy, pageTitle} from '~/lib/copy';

export const meta: Route.MetaFunction = () => [{title: pageTitle(copy.account.title)}, {name: 'robots', content: 'noindex'}];
export const handle = {theme: 'paper'};

export default function Account() {
  return <AccountPage />;
}
