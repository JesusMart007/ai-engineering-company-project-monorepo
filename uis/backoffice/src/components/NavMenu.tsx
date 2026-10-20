"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Inicio" },
  { href: "/incidents", label: "Análisis CSV" },
  { href: "/incidents/new", label: "Registrar incidencia" },
  { href: "/incidents/list", label: "Incidencias" },
  { href: "/incidents/summary", label: "Resumen" },
  { href: "/suppliers", label: "Proveedores" },
  { href: "/inventory/products", label: "Inventario" },
  { href: "/inventory/orders/inbound", label: "Entrada de activos" },
  { href: "/inventory/orders/outbound", label: "Salida de activos" },
  { href: "/inventory/orders", label: "Historial de órdenes" },
  { href: "/account/profile", label: "Mi perfil" },
];

export function NavMenu() {
  const pathname = usePathname();
  return (
    <nav aria-label="Menú principal">
      <ul>
        {LINKS.map(({ href, label }) => (
          <li key={href}>
            <Link href={href} aria-current={pathname === href ? "page" : undefined}>{label}</Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
