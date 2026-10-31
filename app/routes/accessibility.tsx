import {data} from 'react-router';
import type {Route} from './+types/accessibility';
import {AccessibilityPage} from '~/components/pages/AccessibilityPage';
import {ENTRY_COOKIE, readCookie} from '~/lib/cookies';
import {copy, pageMeta} from '~/lib/copy';
import {entryCookie} from '~/lib/entry';

export const meta: Route.MetaFunction = () => pageMeta(copy.accessibility.title);
export const handle = {theme: 'paper'};

export async function loader({request}: Route.LoaderArgs) {
  return {introOn: readCookie(request.headers.get('Cookie'), ENTRY_COOKIE) !== 'off'};
}

/** The intro switch: `off` keeps the opening away for a year; `on` clears the cookie. */
export async function action({request}: Route.ActionArgs) {
  const form = await request.formData();
  const value = form.get('intro') === 'off' ? 'off' : 'on';
  return data({saved: true, introOn: value === 'on'}, {headers: {'Set-Cookie': entryCookie(value)}});
}

export default function Accessibility({loaderData, actionData}: Route.ComponentProps) {
  return <AccessibilityPage introOn={actionData?.introOn ?? loaderData.introOn} saved={Boolean(actionData?.saved)} />;
}
