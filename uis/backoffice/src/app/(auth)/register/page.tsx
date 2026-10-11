"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { TextField } from "@/components/TextField";
import { ApiError } from "@/lib/apiClient";
import { HOME_PATH, setToken } from "@/lib/auth";
import { getUserMessages } from "@/lib/errors";
import { login, register, type RegisterInput } from "@/lib/authApi";

const PROFILE_FIELDS = ["name", "phone", "address"] as const;

export default function RegisterPage() {
  const router = useRouter();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const input: RegisterInput = { email: String(form.get("email")).trim(), password: String(form.get("password")) };
    for (const field of PROFILE_FIELDS) {
      const value = String(form.get(field) ?? "").trim();
      if (value) input[field] = value;
    }

    setFieldErrors({});
    setErrors([]);
    setSubmitting(true);
    let signedIn = false;
    try {
      try {
        await register(input);
      } catch (reason) {
        if (reason instanceof ApiError && Object.keys(reason.fieldErrors).length) setFieldErrors(reason.fieldErrors);
        else setErrors(getUserMessages(reason));
        return;
      }
      try {
        setToken(await login(input.email, input.password));
        signedIn = true;
        router.replace(HOME_PATH);
      } catch {
        setErrors(["La cuenta se creó, pero no se pudo iniciar sesión automáticamente. Inicia sesión manualmente."]);
      }
    } finally {
      // After a successful sign-in the button stays disabled while the home page loads.
      if (!signedIn) setSubmitting(false);
    }
  }

  return (
    <main className="narrow">
      <h1>Crear cuenta</h1>
      <form className="card form-stack" onSubmit={submit}>
        <TextField name="email" label="Email" type="email" autoComplete="email" required error={fieldErrors.email} />
        <TextField
          name="password"
          label="Contraseña"
          type="password"
          autoComplete="new-password"
          required
          hint="Mínimo 8 caracteres."
          error={fieldErrors.password}
        />
        <TextField name="name" label="Nombre" autoComplete="name" error={fieldErrors.name} />
        <TextField name="phone" label="Teléfono" type="tel" autoComplete="tel" error={fieldErrors.phone} />
        <TextField name="address" label="Dirección" autoComplete="street-address" error={fieldErrors.address} />
        {errors.length > 0 && (
          <div className="form-errors" role="alert">
            {errors.map((message) => <p key={message}>{message}</p>)}
          </div>
        )}
        <button type="submit" disabled={submitting}>{submitting ? "Creando cuenta…" : "Crear cuenta"}</button>
      </form>
      <p>
        ¿Ya tienes cuenta? <Link href="/login">Inicia sesión</Link>
      </p>
    </main>
  );
}
