import { ErrorFallback } from "@/components/ErrorFallback";

export default function NotFound() {
  return <ErrorFallback title="Página no encontrada" message="La dirección que has abierto no existe o ha cambiado." />;
}
