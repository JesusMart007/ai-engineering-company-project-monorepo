"use client";

import { Suspense, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { NewPasswordFields, PASSWORDS_DIFFER, passwordsMatch } from "@/components/NewPasswordFields";
import { ApiError } from "@/lib/apiClient";
import { clearToken, LOGIN_PATH } from "@/lib/auth";
import { INVALID_RESET_LINK, resetPassword } from "@/lib/authApi";
import { getUserMessage } from "@/lib/errors";

function ResetPasswordForm() {
  const token = useSearchParams().get("token") ?? "";
  const router = useRouter();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState(token ? "" : INVALID_RESET_LINK);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError("");
    if (!passwordsMatch(form)) {
      setFieldErrors({ confirm_password: PASSWORDS_DIFFER });
      return;
    }
    setFieldErrors({});
    setSubmitting(true);
    let done = false;
    try {
      await resetPassword(token, String(form.get("new_password")));
      clearToken(); // any session in this browser belonged to the old password
      done = true;
      router.replace(`${LOGIN_PATH}?reset=success`);
    } catch (reason) {
      if (reason instanceof ApiError && Object.keys(reason.fieldErrors).length) setFieldErrors(reason.fieldErrors);
      else setError(getUserMessage(reason));
    } finally {
      if (!done) setSubmitting(false);
    }
  }

  return (
    <>
      {token && (
        <form className="card form-stack" onSubmit={submit}>
          <NewPasswordFields errors={fieldErrors} />
          <button type="submit" disabled={submitting}>{submitting ? "Guardando…" : "Cambiar contraseña"}</button>
        </form>
      )}
      {error && (
        <div className="form-errors" role="alert">
          <p>{error}</p>
          <p>
            <Link href="/forgot-password">Solicita un enlace nuevo</Link>
          </p>
        </div>
      )}
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="narrow">
      <h1>Elige una nueva contraseña</h1>
      {/* useSearchParams needs a Suspense boundary in the App Router. */}
      <Suspense fallback={<p className="muted" role="status">Cargando…</p>}>
        <ResetPasswordForm />
      </Suspense>
    </main>
  );
}
