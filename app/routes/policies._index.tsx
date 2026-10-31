import type {Route} from './+types/policies._index';
import {PoliciesIndexPage} from '~/components/pages/PolicyPage';
import {copy, pageMeta} from '~/lib/copy';

export const meta: Route.MetaFunction = () => pageMeta(copy.policies.title);
export const handle = {theme: 'paper'};

export default function Policies() {
  return <PoliciesIndexPage />;
}
