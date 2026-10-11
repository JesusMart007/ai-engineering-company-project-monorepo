"use client";

import { useSyncExternalStore } from "react";
import { getToken, isTokenValid, subscribeToToken } from "@/lib/auth";

export type SessionStatus = "checking" | "authenticated" | "anonymous";

/**
 * Session state read from localStorage. The server render and the first client
 * render (hydration) both see "checking", so protected content never flashes and
 * the markup always matches; the real status arrives right after hydration.
 */
export function useSession(): SessionStatus {
  const token = useSyncExternalStore<string | null | undefined>(subscribeToToken, getToken, () => undefined);
  if (token === undefined) return "checking";
  return isTokenValid(token) ? "authenticated" : "anonymous";
}
