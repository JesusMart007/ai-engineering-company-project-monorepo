"use client";

import { useEffect, useState, type FormEvent } from "react";
import { TextField } from "@/components/TextField";
import { ApiError } from "@/lib/apiClient";
import { getMe, updateProfile, type Me, type ProfileFields } from "@/lib/authApi";

function messageOf(reason: unknown): string {
  return reason instanceof ApiError ? reason.messages.join(" ") : "Error inesperado";
}

export default function ProfilePage() {
  const [me, setMe] = useState<Me | null>(null);
  const [loadError, setLoadError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMe().then(setMe, (reason) => setLoadError(messageOf(reason)));
  }, []);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const text = (field: keyof ProfileFields) => String(form.get(field) ?? "").trim() || null;
    const fields: ProfileFields = { name: text("name"), phone: text("phone"), address: text("address") };

    setFieldErrors({});
    setError("");
    setNotice("");
    setSaving(true);
    try {
      const { name, phone, address } = await updateProfile(fields);
      setMe((current) => current && { ...current, profile: { name, phone, address } });
      setNotice("Perfil guardado.");
    } catch (reason) {
      if (reason instanceof ApiError && Object.keys(reason.fieldErrors).length) setFieldErrors(reason.fieldErrors);
      else setError(messageOf(reason));
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="narrow">
      <h1>Mi perfil</h1>
      {loadError && <p className="error" role="alert">{loadError}</p>}
      {!me && !loadError && <p role="status">Cargando perfil…</p>}
      {me && (
        <form className="card form-stack" onSubmit={save}>
          <label>
            Email
            <input value={me.email} readOnly />
          </label>
          <TextField name="name" label="Nombre" autoComplete="name" defaultValue={me.profile?.name} error={fieldErrors.name} />
          <TextField name="phone" label="Teléfono" type="tel" autoComplete="tel" defaultValue={me.profile?.phone} error={fieldErrors.phone} />
          <TextField
            name="address"
            label="Dirección"
            autoComplete="street-address"
            defaultValue={me.profile?.address}
            error={fieldErrors.address}
          />
          <div aria-live="polite">
            {notice && <p className="success">{notice}</p>}
            {error && <p className="error" role="alert">{error}</p>}
          </div>
          <button type="submit" disabled={saving}>{saving ? "Guardando…" : "Guardar cambios"}</button>
        </form>
      )}
    </main>
  );
}
