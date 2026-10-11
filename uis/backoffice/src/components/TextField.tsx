type TextFieldProps = {
  name: string;
  label: string;
  type?: "text" | "email" | "password" | "tel";
  autoComplete?: string;
  required?: boolean;
  defaultValue?: string | null;
  hint?: string;
  error?: string;
};

/** Labelled input with an optional hint and the API's validation message for that field. */
export function TextField({ name, label, type = "text", autoComplete, required, defaultValue, hint, error }: TextFieldProps) {
  const hintId = hint ? `${name}-hint` : undefined;
  const errorId = error ? `${name}-error` : undefined;
  return (
    <label>
      {label}
      {!required && <small className="muted"> (opcional)</small>}
      <input
        name={name}
        type={type}
        autoComplete={autoComplete}
        required={required}
        defaultValue={defaultValue ?? ""}
        aria-invalid={error ? true : undefined}
        aria-describedby={[hintId, errorId].filter(Boolean).join(" ") || undefined}
      />
      {hint && <small id={hintId} className="muted">{hint}</small>}
      {error && <small id={errorId} className="field-error">{error}</small>}
    </label>
  );
}
