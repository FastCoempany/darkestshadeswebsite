import {formatMoney} from '~/lib/money';
import {cx} from '~/lib/cx';
import type {MoneyV2} from '~/lib/mock/types';

/**
 * The price, always visible, in tabular figures, never lighter than secondary text and never struck
 * through: there are no sales (docs/brief/05-components.md, 08-copy.md).
 */
export function Price({money, variant = 'default', className}: {money: MoneyV2; variant?: 'default' | 'compact'; className?: string}) {
  return (
    <span className={cx('ds-tabular font-text font-book', variant === 'compact' ? 'text-small' : 'text-body', className?.includes('text-ds-') ? className : cx('text-ds-text-primary', className))}>
      {formatMoney(money)}
    </span>
  );
}
