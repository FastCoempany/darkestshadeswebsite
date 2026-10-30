import type {Route} from './+types/policies.$handle';
import {isPolicyHandle, PolicyPage} from '~/components/pages/PolicyPage';
import {copy, pageTitle} from '~/lib/copy';

export const meta: Route.MetaFunction = ({data}) => [{title: pageTitle(data ? copy.policies.items[data.handle] : copy.policies.title)}];
export const handle = {theme: 'paper'};

export async function loader({params}: Route.LoaderArgs) {
  if (!isPolicyHandle(params.handle)) throw new Response('Not found', {status: 404});
  return {handle: params.handle};
}

export default function Policy({loaderData}: Route.ComponentProps) {
  return <PolicyPage handle={loaderData.handle} />;
}
