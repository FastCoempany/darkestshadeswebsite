import {useState, type FormEvent} from 'react';
import {Button} from '~/components/base/Button';
import {Check} from '~/components/base/Check';
import {Field} from '~/components/base/Field';
import {Notice} from '~/components/base/Notice';
import {copy} from '~/lib/copy';
import {cx} from '~/lib/cx';

export type ListState = 'idle' | 'submitting' | 'success' | 'error' | 'already';

export interface ListSubmission {
  email: string;
  phone: string | null;
  smsConsent: boolean;
  scope: string;
}

/** The mock list: records sign-ups in localStorage; no email or SMS provider in this phase (RUN.md, phase 3). */
export async function mockSubmit(s: ListSubmission): Promise<'success' | 'already'> {
  await new Promise((r) => setTimeout(r, 400));
  const key = 'ds_list';
  let existing: string[] = [];
  try {
    existing = JSON.parse(window.localStorage.getItem(key) ?? '[]') as string[];
  } catch {
    existing = [];
  }
  if (existing.includes(s.email.toLowerCase())) return 'already';
  try {
    window.localStorage.setItem(key, JSON.stringify([...existing, s.email.toLowerCase()]));
  } catch {
    // Storage may be unavailable; the sign-up still reports success for the visit.
  }
  return 'success';
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE = /^\+[1-9]\d{6,14}$/;

export interface ListFormProps {
  scope?: 'footer' | 'offer' | 'drop';
  /** Starting state, for stories. */
  initialState?: ListState;
  submit?: (s: ListSubmission) => Promise<'success' | 'already'>;
  onSuccess?: () => void;
  className?: string;
}

/**
 * Email first; the mobile number optional with the consent checkbox, never pre-checked; consent text
 * word for word from en.json (08-copy.md). Email alone is enough to join.
 */
export function ListForm({scope = 'footer', initialState = 'idle', submit = mockSubmit, onSuccess, className}: ListFormProps) {
  const [state, setState] = useState<ListState>(initialState);
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [consent, setConsent] = useState(false);
  const [errors, setErrors] = useState<{email?: string; phone?: string; consent?: string}>({});

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const next: typeof errors = {};
    if (!EMAIL.test(email.trim())) next.email = copy.list.invalidEmail;
    const digits = phone.replace(/[\s().-]/g, '');
    if (digits && !PHONE.test(digits)) next.phone = copy.list.invalidPhone;
    if (digits && !consent) next.consent = copy.list.consentRequired;
    setErrors(next);
    if (Object.keys(next).length) return;
    setState('submitting');
    try {
      const result = await submit({email: email.trim(), phone: digits || null, smsConsent: Boolean(digits) && consent, scope});
      setState(result);
      if (result === 'success') onSuccess?.();
    } catch {
      setState('error');
    }
  }

  if (state === 'success' || state === 'already') {
    return (
      <Notice tone="success" className={className}>
        {state === 'success' ? copy.list.success : copy.list.already}
      </Notice>
    );
  }

  return (
    <form onSubmit={(e) => void onSubmit(e)} noValidate className={cx('grid gap-5', className)} data-list-form={scope} data-state={state}>
      <Field label={copy.list.emailLabel} kind="email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} hint={errors.email} invalid={Boolean(errors.email)} required />
      <p className="font-text text-small text-ds-text-tertiary">{copy.list.emailConsent}</p>
      <Field label={copy.list.phoneLabel} kind="phone" name="phone" value={phone} onChange={(e) => setPhone(e.target.value)} hint={errors.phone} invalid={Boolean(errors.phone)} />
      <Check variant="consent" name="sms" checked={consent} onChange={(e) => setConsent(e.target.checked)} label={copy.list.smsConsent} invalid={Boolean(errors.consent)} error={errors.consent} />
      {state === 'error' ? <Notice tone="error">{copy.list.error}</Notice> : null}
      <Button type="submit" variant="solid" size={48} busy={state === 'submitting'}>
        {copy.list.submit}
      </Button>
    </form>
  );
}
