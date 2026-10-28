import {
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
  useId,
} from "react";

import { fieldControl } from "./styles";

type FieldText = {
  label: string;
  hint?: ReactNode;
  error?: string;
  /** The word shown after the label of required fields, in the page's language. */
  requiredLabel?: string;
};

/** Label, control, hint and inline error, wired together for screen readers. */
function Field({
  id,
  label,
  hint,
  error,
  required,
  requiredLabel,
  children,
}: FieldText & { id: string; required?: boolean; children: ReactNode }) {
  return (
    <div className="grid content-start gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
        {required && requiredLabel && (
          <span className="font-normal text-ink-3"> ({requiredLabel})</span>
        )}
      </label>
      {children}
      {hint && (
        <p id={`${id}-hint`} className="text-sm text-ink-2">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="text-sm text-bad">
          {error}
        </p>
      )}
    </div>
  );
}

function describedBy(id: string, { hint, error }: FieldText) {
  const ids = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean);
  return ids.length ? ids.join(" ") : undefined;
}

export function TextField({
  label,
  hint,
  error,
  requiredLabel,
  ...input
}: FieldText & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  const text = { label, hint, error };
  return (
    <Field
      id={id}
      {...text}
      required={input.required}
      requiredLabel={requiredLabel}
    >
      <input
        id={id}
        aria-describedby={describedBy(id, text)}
        aria-invalid={error ? true : undefined}
        className={fieldControl}
        {...input}
      />
    </Field>
  );
}

export function SelectField({
  label,
  hint,
  error,
  requiredLabel,
  children,
  ...select
}: FieldText & SelectHTMLAttributes<HTMLSelectElement>) {
  const id = useId();
  const text = { label, hint, error };
  return (
    <Field
      id={id}
      {...text}
      required={select.required}
      requiredLabel={requiredLabel}
    >
      <select
        id={id}
        aria-describedby={describedBy(id, text)}
        aria-invalid={error ? true : undefined}
        className={fieldControl}
        {...select}
      >
        {children}
      </select>
    </Field>
  );
}

export function TextAreaField({
  label,
  hint,
  error,
  requiredLabel,
  ...textarea
}: FieldText & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const id = useId();
  const text = { label, hint, error };
  return (
    <Field
      id={id}
      {...text}
      required={textarea.required}
      requiredLabel={requiredLabel}
    >
      <textarea
        id={id}
        aria-describedby={describedBy(id, text)}
        aria-invalid={error ? true : undefined}
        className={`${fieldControl} min-h-28`}
        {...textarea}
      />
    </Field>
  );
}
