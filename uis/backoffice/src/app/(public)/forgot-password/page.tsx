"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { TextField } from "@/components/TextField";
import { forgotPassword } from "@/lib/authApi";
import { getUserMessage, isTransient } from "@/lib/errors";

export default function ForgotPasswordPage() {
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = String(new FormData(event.currentTarget).get("email")).trim();
    setError("");
    setSubmitting(true);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch (reason) {
      // The API answers 200 for every email, so a failure here never depends on whether
      // the email exists: only a dropped connection, a timeout or a server error is reported.
      if (isTransient(reason)) setError(getUserMessage(reason));
      else setSent(true);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="narrow">
      <h1>¿Olvidaste tu contraseña?</h1>
      <p className="muted">Escribe el email de tu cuenta y te enviaremos un enlace para elegir una nueva.</p>
      <form className="card form-stack" onSubmit={submit}>
        <fieldset disabled={submitting || sent} className="form-stack plain">
          <TextField name="email" label="Email" type="email" autoComplete="email" required />
          <button type="submit">{submitting ? "Enviando…" : "Enviar enlace"}</button>
        </fieldset>
        <div aria-live="polite">
          {sent && <p className="success">Si esa dirección está registrada, recibirás un enlace en breve.</p>}
          {error && <p className="error" role="alert">{error}</p>}
        </div>
      </form>
      <p>
        <Link href="/login">Volver a iniciar sesión</Link>
      </p>
    </main>
  );
}
