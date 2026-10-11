'use client'; // Error boundaries must be Client Components

import './globals.css';
import ErrorState from '../components/ErrorState';

// Last resort for errors in the root layout itself: it replaces the layout, so it renders its own document.
export default function GlobalError({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <html lang="es">
      <body className="min-h-full bg-slate-50 dark:bg-slate-950 font-sans">
        <title>Error · Talent Pipeline Tracker</title>
        <main className="max-w-3xl mx-auto w-full px-4 py-10">
          <ErrorState
            title="Algo ha salido mal"
            message="No hemos podido cargar la aplicación. Inténtalo de nuevo en unos minutos."
            onRetry={() => retry()}
          />
        </main>
      </body>
    </html>
  );
}
