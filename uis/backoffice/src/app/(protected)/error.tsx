"use client"; // Error boundaries must be Client Components

import { ErrorFallback } from "@/components/ErrorFallback";

// Same as app/error.tsx, but inside the protected layout, so the top bar and menu stay.
export default function ProtectedError({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return <ErrorFallback message="No hemos podido mostrar esta página. Inténtalo de nuevo." onRetry={() => retry()} />;
}
