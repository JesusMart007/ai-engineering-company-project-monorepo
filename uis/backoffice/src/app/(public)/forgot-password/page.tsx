"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { TextField } from "@/components/TextField";
import { forgotPassword } from "@/lib/authApi";

export default function ForgotPasswordPage() {
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = String(new FormData(event.currentTarget).get("email")).trim();
    setSubmitting(true);
    try {
      await forgotPassword(email);
    } catch {
      // Same answer whatever happens: the page must not reveal whether the email exists.
    }
    setSent(true);
    setSubmitting(false);
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
        </div>
      </form>
      <p>
        <Link href="/login">Volver a iniciar sesión</Link>
      </p>
    </main>
  );
}
