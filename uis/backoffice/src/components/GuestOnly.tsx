"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { SessionCheck } from "@/components/SessionCheck";
import { HOME_PATH } from "@/lib/auth";
import { useSession } from "@/lib/useSession";

/** For /login and /register: someone already signed in goes straight to the home view. */
export function GuestOnly({ children }: { children: React.ReactNode }) {
  const status = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated") router.replace(HOME_PATH);
  }, [status, router]);

  return status === "anonymous" ? children : <SessionCheck />;
}
