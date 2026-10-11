import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "Nexova Backoffice", description: "Backoffice interno de Nexova" };

// The top bar lives in the (auth) and (protected) group layouts: only signed-in users see the menu.
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
