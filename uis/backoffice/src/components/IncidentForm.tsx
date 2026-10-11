"use client";

import { useState, type FormEvent } from "react";
import {
  ApiError,
  BRANCHES,
  BRANCH_LABELS,
  INCIDENT_CATEGORIES,
  INCIDENT_CATEGORY_DESCRIPTIONS,
  INCIDENT_CATEGORY_LABELS,
  INCIDENT_ORIGINS,
  INCIDENT_ORIGIN_DESCRIPTIONS,
  INCIDENT_ORIGIN_LABELS,
  INCIDENT_STATUS_LABELS,
  createIncident,
  type Branch,
  type Incident,
  type IncidentCategory,
  type IncidentOrigin,
} from "@/lib/incidentsApi";

type Values = { title: string; description: string; category: IncidentCategory | ""; origin: IncidentOrigin | ""; branch: Branch | "" };
type Field = keyof Values;

const EMPTY: Values = { title: "", description: "", category: "", origin: "", branch: "" };
const TITLE_MAX_LENGTH = 120;
const FIELDS: Field[] = ["title", "description", "category", "origin", "branch"];
const REQUIRED_MESSAGES: Record<Field, string> = {
  title: "El título es obligatorio",
  description: "La descripción es obligatoria",
  category: "Selecciona una categoría",
  origin: "Selecciona el origen",
  branch: "Selecciona la sede",
};
const GENERAL_ERROR = "No se pudo registrar la incidencia. Inténtalo de nuevo en unos minutos.";

function validate(values: Values): Partial<Record<Field, string>> {
  const errors: Partial<Record<Field, string>> = {};
  for (const field of FIELDS) if (!values[field].trim()) errors[field] = REQUIRED_MESSAGES[field];
  if (values.title.trim().length > TITLE_MAX_LENGTH) errors.title = `El título no puede superar ${TITLE_MAX_LENGTH} caracteres`;
  return errors;
}

/** Field messages from a 400 the user can fix; anything else gets one general, non-technical message. */
function apiErrors(reason: unknown): { fields: Partial<Record<Field, string>>; general: string } {
  if (reason instanceof ApiError && reason.status === 400) {
    const fields: Partial<Record<Field, string>> = {};
    for (const field of FIELDS) if (reason.fieldErrors[field]) fields[field] = reason.fieldErrors[field];
    if (Object.keys(fields).length > 0) return { fields, general: "" };
  }
  return { fields: {}, general: GENERAL_ERROR };
}

export function IncidentForm() {
  const [values, setValues] = useState<Values>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({});
  const [generalError, setGeneralError] = useState("");
  const [created, setCreated] = useState<Incident | null>(null);
  const [saving, setSaving] = useState(false);
  const fromBranch = values.origin === "branch";

  function set<K extends Field>(field: K, value: Values[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function describedBy(field: Field, hint = false): string | undefined {
    return [hint && `${field}-hint`, errors[field] && `${field}-error`].filter(Boolean).join(" ") || undefined;
  }

  function fieldError(field: Field) {
    return errors[field] && <small id={`${field}-error`} className="field-error">{errors[field]}</small>;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setCreated(null);
    setGeneralError("");
    const problems = validate(values);
    setErrors(problems);
    if (Object.keys(problems).length > 0) return;
    setSaving(true);
    try {
      const incident = await createIncident({
        title: values.title.trim(),
        description: values.description.trim(),
        category: values.category as IncidentCategory,
        origin: values.origin as IncidentOrigin,
        branch: values.branch as Branch,
      });
      setValues(EMPTY);
      setCreated(incident);
    } catch (reason) {
      const { fields, general } = apiErrors(reason);
      setErrors(fields);
      setGeneralError(general);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card incident-form" onSubmit={submit} noValidate aria-busy={saving}>
      <div aria-live="polite">
        {created && (
          <p className="success" role="status">
            Incidencia #{created.id} «{created.title}» registrada como {INCIDENT_STATUS_LABELS[created.status].toLowerCase()}.
          </p>
        )}
      </div>
      <fieldset className="plain form-stack" disabled={saving}>
        <label>
          Título *
          <input
            value={values.title}
            maxLength={TITLE_MAX_LENGTH}
            aria-required="true"
            aria-invalid={errors.title ? true : undefined}
            aria-describedby={describedBy("title", true)}
            onChange={(event) => set("title", event.target.value)}
          />
          <small id="title-hint" className="muted">Resumen breve (máximo {TITLE_MAX_LENGTH} caracteres).</small>
          {fieldError("title")}
        </label>
        <label>
          Descripción *
          <textarea
            rows={4}
            value={values.description}
            aria-required="true"
            aria-invalid={errors.description ? true : undefined}
            aria-describedby={describedBy("description")}
            onChange={(event) => set("description", event.target.value)}
          />
          {fieldError("description")}
        </label>
        <div className="form-grid">
          <label>
            Categoría *
            <select
              value={values.category}
              aria-required="true"
              aria-invalid={errors.category ? true : undefined}
              aria-describedby={describedBy("category", Boolean(values.category))}
              onChange={(event) => set("category", event.target.value as IncidentCategory | "")}
            >
              <option value="">Selecciona una categoría…</option>
              {INCIDENT_CATEGORIES.map((value) => <option key={value} value={value}>{INCIDENT_CATEGORY_LABELS[value]}</option>)}
            </select>
            {values.category && <small id="category-hint" className="muted">{INCIDENT_CATEGORY_DESCRIPTIONS[values.category]}</small>}
            {fieldError("category")}
          </label>
          <label>
            Origen *
            <select
              value={values.origin}
              aria-required="true"
              aria-invalid={errors.origin ? true : undefined}
              aria-describedby={describedBy("origin", Boolean(values.origin))}
              onChange={(event) => set("origin", event.target.value as IncidentOrigin | "")}
            >
              <option value="">Selecciona el origen…</option>
              {INCIDENT_ORIGINS.map((value) => <option key={value} value={value}>{INCIDENT_ORIGIN_LABELS[value]}</option>)}
            </select>
            {values.origin && <small id="origin-hint" className="muted">{INCIDENT_ORIGIN_DESCRIPTIONS[values.origin]}</small>}
            {fieldError("origin")}
          </label>
          <label className={fromBranch ? "highlight" : undefined}>
            Sede *
            <select
              value={values.branch}
              aria-required="true"
              aria-invalid={errors.branch ? true : undefined}
              aria-describedby={describedBy("branch", true)}
              onChange={(event) => set("branch", event.target.value as Branch | "")}
            >
              <option value="">Selecciona la sede…</option>
              {BRANCHES.map((value) => <option key={value} value={value}>{BRANCH_LABELS[value]}</option>)}
            </select>
            <small id="branch-hint" className={fromBranch ? "highlight-text" : "muted"}>
              {fromBranch
                ? "Estás reportando desde una sede: confirma cuál."
                : "Si no corresponde a una oficina concreta, elige «Central — Sede Valencia»."}
            </small>
            {fieldError("branch")}
          </label>
          <label>
            Estado
            <input value={INCIDENT_STATUS_LABELS.open} readOnly aria-describedby="status-hint" />
            <small id="status-hint" className="muted">Toda incidencia nueva se registra como abierta.</small>
          </label>
        </div>
      </fieldset>
      {generalError && (
        <div className="form-errors" role="alert">
          <p>{generalError}</p>
        </div>
      )}
      <div className="actions">
        <button type="submit" disabled={saving}>
          {saving ? <><span className="spinner" aria-hidden="true" />Registrando…</> : "Registrar incidencia"}
        </button>
      </div>
    </form>
  );
}
