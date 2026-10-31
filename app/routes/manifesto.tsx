import type {Route} from './+types/manifesto';
import {ManifestoPage} from '~/components/pages/ManifestoPage';
import {copy, pageMeta} from '~/lib/copy';

export const meta: Route.MetaFunction = () => pageMeta(copy.manifesto.title);
export const handle = {theme: 'paper'};

export default function Manifesto() {
  return <ManifestoPage />;
}
