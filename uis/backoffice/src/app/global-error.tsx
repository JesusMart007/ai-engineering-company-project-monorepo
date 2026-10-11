"use client"; // Error boundaries must be Client Components

import "./globals.css";
import { ErrorFallback } from "@/components/ErrorFallback";

// Last resort for errors in the root layout itself: it replaces the layout, so it renders its own document.
export default function GlobalError({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <html lang="es">
      <body>
        <title>Error · Nexova Backoffice</title>
        <ErrorFallback message="No hemos podido cargar el backoffice. Inténtalo de nuevo en unos minutos." onRetry={() => retry()} />
      </body>
    </html>
  );
}
