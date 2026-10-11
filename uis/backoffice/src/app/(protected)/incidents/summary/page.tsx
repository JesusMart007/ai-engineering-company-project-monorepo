import Link from "next/link";
import { IncidentTotals } from "@/components/IncidentTotals";

export default function IncidentSummaryPage() {
  return (
    <main className="wide">
      <div className="page-header">
        <div>
          <h1>Resumen de incidencias</h1>
          <p className="muted">Totales por estado, categoría, origen y sede de todas las incidencias registradas.</p>
        </div>
        <Link className="button secondary" href="/incidents/list">Ver incidencias</Link>
      </div>
      <IncidentTotals />
    </main>
  );
}
