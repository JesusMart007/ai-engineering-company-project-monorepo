import Link from "next/link";

export default function Home() {
  return (
    <main>
      <h1>Backoffice Nexova</h1>
      <section className="card">
        <h2>Análisis de incidencias</h2>
        <p>Sube el CSV de tickets de soporte y obtén métricas por categoría, estado y satisfacción, junto con el detalle de los registros inválidos.</p>
        <Link className="button" href="/incidents">Ir al análisis de incidencias</Link>
      </section>
      <section className="card">
        <h2>Gestor de incidencias</h2>
        <p>Registra fallos técnicos, quejas de clientes, errores de proceso o incidencias de personal, sigue su estado y consulta los totales por sede.</p>
        <div className="actions">
          <Link className="button" href="/incidents/new">Registrar incidencia</Link>
          <Link className="button secondary" href="/incidents/list">Ver incidencias</Link>
          <Link className="button secondary" href="/incidents/summary">Resumen</Link>
        </div>
      </section>
      <section className="card">
        <h2>Proveedores</h2>
        <p>Consulta el directorio oficial de proveedores, filtra por país o categoría, registra altas y actualiza tarifas y estados.</p>
        <Link className="button" href="/suppliers">Ir a proveedores</Link>
      </section>
    </main>
  );
}
