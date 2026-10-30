import type {MoneyV2} from '~/lib/mock/types';

/** "$100" for 100.00 USD; cents only when there are any. Never hidden, never struck through. */
export function formatMoney(money: MoneyV2): string {
  const amount = Number(money.amount);
  const whole = Number.isInteger(amount);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: money.currencyCode,
    minimumFractionDigits: whole ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(amount);
}
