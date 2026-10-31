import {redirect} from 'react-router';

/** /drops has no page of its own: it goes where /drop goes (04 lists /drop and /drops/{number}). */
export async function loader() {
  return redirect('/drop');
}
