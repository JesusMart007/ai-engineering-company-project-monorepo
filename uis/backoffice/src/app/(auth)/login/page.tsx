"use client";

import { Suspense, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { TextField } from "@/components/TextField";
import { ApiError } from "@/lib/apiClient";
import { HOME_PATH, setToken } from "@/lib/auth";
import { login } from "@/lib/authApi";

function LoginForm() {
  const router = useRouter();
  const passwordReset = useSearchParams().get("reset") === "success";
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError("");
    setSubmitting(true);
    try {
      setToken(await login(String(form.get("email")).trim(), String(form.get("password"))));
      router.replace(HOME_PATH);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.messages.join(" ") : "Error inesperado");
      setSubmitting(false);
    }
  }

  return (
    <>
      {passwordReset && <p className="success" role="status">Contraseña actualizada, inicia sesión.</p>}
      <form className="card form-stack" onSubmit={submit}>
        <TextField name="email" label="Email" type="email" autoComplete="email" required />
        <TextField name="password" label="Contraseña" type="password" autoComplete="current-password" required />
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={submitting}>{submitting ? "Entrando…" : "Entrar"}</button>
        <Link href="/forgot-password">¿Olvidaste tu contraseña?</Link>
      </form>
    </>
  );
}

export default function LoginPage() {
  return (
    <main className="narrow">
      <h1>Iniciar sesión</h1>
      {/* useSearchParams (the ?reset=success notice) needs a Suspense boundary in the App Router. */}
      <Suspense>
        <LoginForm />
      </Suspense>
      <p>
        ¿No tienes cuenta? <Link href="/register">Regístrate</Link>
      </p>
    </main>
  );
}
