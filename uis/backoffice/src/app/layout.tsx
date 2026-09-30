import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentHub | Nexova",
  description: "Centro ejecutivo de operaciones de Nexova Solutions.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}