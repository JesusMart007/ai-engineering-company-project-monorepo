"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { NewPasswordFields, PASSWORDS_DIFFER, passwordsMatch } from "@/components/NewPasswordFields";
import { TextField } from "@/components/TextField";
import { ApiError } from "@/lib/apiClient";
import { changePassword } from "@/lib/authApi";

export default function ChangePasswordPage() {
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setError("");
    setNotice("");
    if (!passwordsMatch(form)) {
      setFieldErrors({ confirm_password: PASSWORDS_DIFFER });
      return;
    }
    setFieldErrors({});
    setSaving(true);
    try {
      await changePassword(String(form.get("current_password")), String(form.get("new_password")));
      formElement.reset();
      setNotice("Contraseña actualizada. Úsala la próxima vez que inicies sesión.");
    } catch (reason) {
      if (reason instanceof ApiError && Object.keys(reason.fieldErrors).length) setFieldErrors(reason.fieldErrors);
      else setError(reason instanceof ApiError ? reason.messages.join(" ") : "Error inesperado");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="narrow">
      <h1>Cambiar contraseña</h1>
      <form className="card form-stack" onSubmit={save}>
        <TextField
          name="current_password"
          label="Contraseña actual"
          type="password"
          autoComplete="current-password"
          required
          error={fieldErrors.current_password}
        />
        <NewPasswordFields errors={fieldErrors} />
        <div aria-live="polite">
          {notice && <p className="success">{notice}</p>}
          {error && <p className="error" role="alert">{error}</p>}
        </div>
        <button type="submit" disabled={saving}>{saving ? "Guardando…" : "Cambiar contraseña"}</button>
      </form>
      <p>
        <Link href="/account/profile">Volver a mi perfil</Link>
      </p>
    </main>
  );
}
