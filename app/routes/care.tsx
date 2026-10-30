import type {Route} from './+types/care';
import {CarePage} from '~/components/pages/CarePage';
import {copy, pageTitle} from '~/lib/copy';

export const meta: Route.MetaFunction = () => [{title: pageTitle(copy.care.title)}];
export const handle = {theme: 'paper'};

export default function Care() {
  return <CarePage />;
}
