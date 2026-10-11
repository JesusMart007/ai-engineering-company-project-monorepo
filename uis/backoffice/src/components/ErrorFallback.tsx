import Link from "next/link";
import { SUPPORT_EMAIL } from "@/lib/errors";

type Props = { title?: string; message: string; onRetry?: () => void };

/** Full-page error state with a way out: retry, home and support contact. */
export function ErrorFallback({ title = "Algo ha salido mal", message, onRetry }: Props) {
  return (
    <main className="narrow">
      <section className="card" role="alert">
        <h1>{title}</h1>
        <p>{message}</p>
        <div className="actions">
          {onRetry && <button type="button" onClick={onRetry}>Reintentar</button>}
          <Link className={onRetry ? "button secondary" : "button"} href="/">Volver al inicio</Link>
        </div>
        <p className="muted small">
          Si el problema continúa, escríbenos a <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>.
        </p>
      </section>
    </main>
  );
}
