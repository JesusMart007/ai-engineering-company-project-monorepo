"use client";

import { logout } from "@/lib/auth";

export function LogoutButton() {
  return (
    <button type="button" className="logout" onClick={logout}>
      Cerrar sesión
    </button>
  );
}
