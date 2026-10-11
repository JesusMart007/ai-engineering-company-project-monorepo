"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BRANCHES,
  BRANCH_LABELS,
  INCIDENT_CATEGORIES,
  INCIDENT_CATEGORY_LABELS,
  INCIDENT_ORIGINS,
  INCIDENT_ORIGIN_LABELS,
  INCIDENT_STATUSES,
  INCIDENT_STATUS_LABELS,
  getIncidentTotals,
  type IncidentTotals as Totals,
} from "@/lib/incidentsApi";

const LOAD_ERROR = "No se pudo cargar el resumen. Comprueba tu conexión e inténtalo de nuevo.";

function pct(count: number, total: number): string {
  return total ? `${((count / total) * 100).toFixed(1)}%` : "0.0%";
}

function Breakdown<K extends string>(props: { title: string; keys: readonly K[]; labels: Record<K, string>; counts: Record<K, number>; total: number }) {
  const { title, keys, labels, counts, total } = props;
  return (
    <section>
      <h3>{title}</h3>
      <table>
        <thead><tr><th scope="col">Valor</th><th scope="col" className="num">Incidencias</th><th scope="col" className="num">%</th><th scope="col" aria-hidden="true" /></tr></thead>
        <tbody>
          {keys.map((key) => {
            const count = counts[key] ?? 0;
            return (
              <tr key={key}>
                <td>{labels[key]}</td>
                <td className="num">{count}</td>
                <td className="num">{pct(count, total)}</td>
                <td className="bar-cell" aria-hidden="true"><span className="bar" style={{ width: pct(count, total) }} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

/** Totals from GET /api/incidents/summary. Handles its own loading and error states, so a failure never breaks the page. */
export function IncidentTotals() {
  const [totals, setTotals] = useState<Totals | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setTotals(await getIncidentTotals());
    } catch {
      setTotals(null);
      setError(LOAD_ERROR);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Fetching on mount is the point of this effect; load() flags "loading" first.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  if (loading) {
    return (
      <section className="card" aria-busy="true">
        <p className="state muted"><span className="spinner" aria-hidden="true" />Cargando resumen…</p>
      </section>
    );
  }
  if (error || !totals) {
    return (
      <section className="card">
        <div className="state" role="alert">
          <p className="error">{error || LOAD_ERROR}</p>
          <button type="button" onClick={load}>Reintentar</button>
        </div>
      </section>
    );
  }

  const open = totals.by_status.open + totals.by_status.in_progress;
  return (
    <>
      <section className="card" aria-label="Totales">
        <div className="stats">
          <div className="stat"><span>Incidencias registradas</span><strong>{totals.total}</strong></div>
          <div className="stat"><span>Sin resolver (abiertas + en curso)</span><strong>{open}</strong></div>
          <div className="stat"><span>Incumplimientos de SLA</span><strong className={totals.by_category.sla_breach ? "danger" : ""}>{totals.by_category.sla_breach}</strong></div>
          <div className="stat"><span>Resueltas</span><strong>{totals.by_status.resolved}</strong></div>
        </div>
        {totals.total === 0 && <p className="muted">Todavía no hay incidencias: todos los totales están a cero.</p>}
        <div className="actions">
          <button type="button" className="secondary small" onClick={load}>Actualizar</button>
        </div>
      </section>
      <section className="card totals-grid">
        <Breakdown title="Por estado" keys={INCIDENT_STATUSES} labels={INCIDENT_STATUS_LABELS} counts={totals.by_status} total={totals.total} />
        <Breakdown title="Por categoría" keys={INCIDENT_CATEGORIES} labels={INCIDENT_CATEGORY_LABELS} counts={totals.by_category} total={totals.total} />
        <Breakdown title="Por origen" keys={INCIDENT_ORIGINS} labels={INCIDENT_ORIGIN_LABELS} counts={totals.by_origin} total={totals.total} />
        <Breakdown title="Por sede" keys={BRANCHES} labels={BRANCH_LABELS} counts={totals.by_branch} total={totals.total} />
      </section>
    </>
  );
}
