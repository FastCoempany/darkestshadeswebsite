import type {Route} from './+types/policies._index';
import {PoliciesIndexPage} from '~/components/pages/PolicyPage';
import {copy, pageTitle} from '~/lib/copy';

export const meta: Route.MetaFunction = () => [{title: pageTitle(copy.policies.title)}];
export const handle = {theme: 'paper'};

export default function Policies() {
  return <PoliciesIndexPage />;
}
