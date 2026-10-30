import {redirect} from 'react-router';
import type {Route} from './+types/drop';

/** /drop points to the live or next drop, else the latest (04). */
export async function loader({context}: Route.LoaderArgs) {
  const current = context.store.drops.current();
  return redirect(current ? `/drops/${current.number}` : '/frames');
}
