import Link from "next/link";
import { IncidentForm } from "@/components/IncidentForm";

export default function NewIncidentPage() {
  return (
    <main>
      <div className="page-header">
        <div>
          <h1>Registrar incidencia</h1>
          <p className="muted">Fallos técnicos, quejas de clientes, errores de proceso o incidencias de personal: todo en un único registro.</p>
        </div>
        <Link className="button secondary" href="/incidents/list">Ver incidencias</Link>
      </div>
      <IncidentForm />
    </main>
  );
}
