import {TextLink} from '~/components/base/TextLink';
import {ListForm} from '~/components/house/ListForm';
import {Logo} from '~/components/house/Logo';
import {Seal} from '~/components/house/Seal';
import {copy, fill, instagramUrl} from '~/lib/copy';

const COLUMNS = [
  {title: copy.footer.columns.shop, links: [{to: '/drop', label: copy.nav.drop}, {to: '/frames', label: copy.nav.frames}]},
  {title: copy.footer.columns.house, links: [{to: '/manifesto', label: copy.nav.manifesto}, {to: '/cast', label: copy.nav.cast}]},
  {
    title: copy.footer.columns.help,
    links: [
      {to: '/questions', label: copy.footer.links.questions},
      {to: '/care', label: copy.footer.links.care},
      {to: '/policies/shipping', label: copy.footer.links.shipping},
      {to: '/policies/exchange', label: copy.footer.links.exchange},
      {to: '/policies/warranty', label: copy.footer.links.warranty},
    ],
  },
  {
    title: copy.footer.columns.legal,
    links: [
      {to: '/policies/privacy', label: copy.footer.links.privacy},
      {to: '/policies/terms', label: copy.footer.links.terms},
      {to: '/policies/sms-terms', label: copy.footer.links.smsTerms},
      {to: '/accessibility', label: copy.footer.links.accessibility},
    ],
  },
];

/** The list sign-up, the link columns, Instagram, the GCD seal, and the horizontal logo edge to edge at the very bottom. */
export function Footer({year, showList = true}: {year: number; showList?: boolean}) {
  return (
    <footer className="grid gap-12 border-t border-ds-border-hairline bg-ds-surface-canvas px-4 pt-12 text-ds-text-primary md:px-6 lg:px-10 xl:px-14" data-footer>
      {showList ? (
        <section aria-labelledby="footer-list" className="grid gap-6 lg:grid-cols-2 lg:gap-12">
          <h2 id="footer-list" className="ds-display text-h2 leading-heading tracking-heading">
            {copy.list.title}
          </h2>
          <ListForm scope="footer" />
        </section>
      ) : null}
      <nav aria-label={copy.footer.navLabel} className="grid grid-cols-2 gap-8 md:grid-cols-4">
        {COLUMNS.map((col) => (
          <div key={col.title} className="grid content-start gap-3">
            <h2 className="ds-display text-label leading-ui tracking-label text-ds-text-secondary">{col.title}</h2>
            <ul className="grid gap-2">
              {col.links.map((l) => (
                <li key={l.to}>
                  <TextLink to={l.to} variant="footer">
                    {l.label}
                  </TextLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div className="grid gap-2">
          <TextLink to={instagramUrl()} variant="footer" external>
            {copy.meta.instagram}
          </TextLink>
          <p className="font-text text-micro text-ds-text-tertiary">{fill(copy.footer.copyright, {year})}</p>
        </div>
        <Seal width={96} />
      </div>
      <div className="-mx-4 pb-4 md:-mx-6 lg:-mx-10 xl:-mx-14">
        <Logo variant="horizontal" className="!h-auto w-full" />
      </div>
    </footer>
  );
}
