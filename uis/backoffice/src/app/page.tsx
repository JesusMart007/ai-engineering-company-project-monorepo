const metrics = [
  { label: "Ingresos", value: "$1.84M", change: "+8.2%", tone: "green" },
  { label: "SLA cumplido", value: "94.6%", change: "+1.4%", tone: "blue" },
  { label: "Tiempo de contratación", value: "31 días", change: "-3 días", tone: "orange" },
  { label: "Leads generados", value: "486", change: "+12.7%", tone: "red" },
];

const alerts = [
  { level: "Crítica", area: "Soporte", detail: "SLA regional bajo el umbral del 90%", time: "Hace 18 min" },
  { level: "Alta", area: "Selección", detail: "Cinco posiciones superan 45 días abiertas", time: "Hace 2 h" },
  { level: "Media", area: "Marketing", detail: "Conversión semanal por debajo del objetivo", time: "Ayer" },
];

export default function Dashboard() {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div>
          <p className="brand">Nexova</p>
          <p className="product">AgentHub</p>
        </div>
        <nav aria-label="Navegación del backoffice">
          <a className="active" href="#dashboard">Resumen</a>
          <a href="#alerts">Alertas <span>3</span></a>
          <a href="#reports">Reportes</a>
          <a href="#departments">Departamentos</a>
        </nav>
        <div className="profile">
          <span aria-hidden="true">LM</span>
          <div><strong>Laura Mendoza</strong><small>CEO</small></div>
        </div>
      </aside>

      <section className="workspace" id="dashboard">
        <header className="topbar">
          <div>
            <p>Domingo, 20 de septiembre</p>
            <h1>Resumen ejecutivo</h1>
          </div>
          <button type="button">Generar reporte</button>
        </header>

        <section className="metrics" aria-label="Indicadores principales">
          {metrics.map((metric) => (
            <article key={metric.label} className={`metric ${metric.tone}`}>
              <p>{metric.label}</p>
              <strong>{metric.value}</strong>
              <span>{metric.change} esta semana</span>
            </article>
          ))}
        </section>

        <div className="contentGrid">
          <section className="panel chartPanel" aria-labelledby="trend-title">
            <div className="panelHeader">
              <div><p>Rendimiento</p><h2 id="trend-title">Pulso de la operación</h2></div>
              <span>Últimas 6 semanas</span>
            </div>
            <div className="chart" role="img" aria-label="Tendencia ascendente del rendimiento operativo">
              {[44, 58, 51, 69, 74, 86].map((height, index) => <i key={index} style={{ height: `${height}%` }} />)}
            </div>
            <div className="chartLabels"><span>S32</span><span>S33</span><span>S34</span><span>S35</span><span>S36</span><span>S37</span></div>
          </section>

          <section className="panel alerts" id="alerts" aria-labelledby="alerts-title">
            <div className="panelHeader"><div><p>Atención</p><h2 id="alerts-title">Alertas activas</h2></div><strong>03</strong></div>
            <div>
              {alerts.map((alert) => (
                <article key={alert.detail}>
                  <span className={`badge ${alert.level.toLowerCase()}`}>{alert.level}</span>
                  <div><strong>{alert.area}</strong><p>{alert.detail}</p><small>{alert.time}</small></div>
                </article>
              ))}
            </div>
          </section>
        </div>

        <section className="activity" id="reports">
          <div><p>Actividad reciente</p><h2>Lo que cambió hoy</h2></div>
          <ol>
            <li><time>09:42</time><span>Reporte semanal generado</span><strong>Dirección</strong></li>
            <li><time>08:15</time><span>Snapshot de KPIs actualizado</span><strong>6 áreas</strong></li>
            <li><time>07:50</time><span>Alerta de SLA abierta</span><strong>Soporte</strong></li>
          </ol>
        </section>
      </section>
    </main>
  );
}