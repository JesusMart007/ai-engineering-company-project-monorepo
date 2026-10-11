import { TextField } from "@/components/TextField";

export const PASSWORDS_DIFFER = "Las contraseñas no coinciden.";

/** "new_password" and "confirm_password" inputs; check them with `passwordsMatch` before calling the API. */
export function NewPasswordFields({ errors }: { errors: Record<string, string> }) {
  return (
    <>
      <TextField
        name="new_password"
        label="Nueva contraseña"
        type="password"
        autoComplete="new-password"
        required
        hint="Mínimo 8 caracteres."
        error={errors.new_password}
      />
      <TextField
        name="confirm_password"
        label="Repite la nueva contraseña"
        type="password"
        autoComplete="new-password"
        required
        error={errors.confirm_password}
      />
    </>
  );
}

export function passwordsMatch(form: FormData): boolean {
  return form.get("new_password") === form.get("confirm_password");
}
