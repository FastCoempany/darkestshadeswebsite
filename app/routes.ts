import {flatRoutes} from '@react-router/fs-routes';
import {type RouteConfig} from '@react-router/dev/routes';
import {hydrogenRoutes} from '@shopify/hydrogen';

/** File-based routes in app/routes/. `account.$.tsx` is the placeholder for /account and everything under it. */
export default hydrogenRoutes([...(await flatRoutes())]) satisfies RouteConfig;
