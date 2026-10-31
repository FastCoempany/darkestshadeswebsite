import type {Route} from './+types/care';
import {CarePage} from '~/components/pages/CarePage';
import {copy, pageMeta} from '~/lib/copy';

export const meta: Route.MetaFunction = () => pageMeta(copy.care.title);
export const handle = {theme: 'paper'};

export default function Care() {
  return <CarePage />;
}
