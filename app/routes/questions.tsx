import type {Route} from './+types/questions';
import {QuestionsPage} from '~/components/pages/QuestionsPage';
import {copy, pageMeta} from '~/lib/copy';

export const meta: Route.MetaFunction = () => pageMeta(copy.questions.title);
export const handle = {theme: 'paper'};

export default function Questions() {
  return <QuestionsPage />;
}
