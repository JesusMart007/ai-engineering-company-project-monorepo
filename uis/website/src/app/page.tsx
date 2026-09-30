const services = [
  {
    eyebrow: "Selección",
    title: "Talento que mueve el negocio",
    description: "Procesos de búsqueda y evaluación conectados con las prioridades reales de cada equipo.",
  },
  {
    eyebrow: "Desarrollo",
    title: "Capacidades que permanecen",
    description: "Programas de formación diseñados para convertir estrategia en hábitos de liderazgo.",
  },
  {
    eyebrow: "Operaciones",
    title: "Decisiones con mejor señal",
    description: "AgentHub reúne indicadores y alertas para que la dirección actúe con contexto actualizado.",
  },
];

export default function Home() {
  return (
    <main>
      <header className="siteHeader">
        <a className="brand" href="#inicio" aria-label="Nexova, inicio">Nexova</a>
        <nav aria-label="Navegación principal">
          <a href="#servicios">Servicios</a>
          <a href="#agenthub">AgentHub</a>
          <a href="mailto:contacto@nexova.com">Contacto</a>
        </nav>
      </header>

      <section className="hero" id="inicio">
        <div className="heroContent">
          <p className="kicker">Consultoría de talento · Chile + Argentina</p>
          <h1>Personas brillantes. Operaciones más claras.</h1>
          <p className="lead">Ayudamos a equipos en crecimiento a contratar, desarrollar y dirigir talento con una combinación rigurosa de experiencia humana y datos.</p>
          <a className="primaryAction" href="#servicios">Conoce nuestro enfoque <span aria-hidden="true">→</span></a>
        </div>
        <aside className="signalPanel" aria-label="Indicadores de impacto">
          <p>Señal ejecutiva</p>
          <strong>6 áreas</strong>
          <span>conectadas en una visión operativa</span>
          <div className="signalLine"><i /><i /><i /><i /><i /></div>
        </aside>
      </section>

      <section className="services" id="servicios" aria-labelledby="services-title">
        <div className="sectionIntro">
          <p className="kicker">Qué hacemos</p>
          <h2 id="services-title">De la búsqueda de talento a la inteligencia operativa.</h2>
        </div>
        <div className="serviceGrid">
          {services.map((service, index) => (
            <article key={service.title}>
              <span>0{index + 1}</span>
              <p>{service.eyebrow}</p>
              <h3>{service.title}</h3>
              <div className="rule" />
              <p>{service.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="agentHub" id="agenthub">
        <p className="kicker">AgentHub</p>
        <h2>El pulso de Nexova, en un solo lugar.</h2>
        <p>Indicadores, alertas y reportes ejecutivos que convierten datos dispersos en decisiones trazables.</p>
        <a href="mailto:contacto@nexova.com">Hablar con nuestro equipo</a>
      </section>

      <footer>
        <span>Nexova Solutions</span>
        <span>Chile · Argentina</span>
      </footer>
    </main>
  );
}