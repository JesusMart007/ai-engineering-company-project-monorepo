"use client";

import { useCallback, useEffect, useState } from "react";
import { getUserMessage } from "@/lib/errors";
import { getProducts, type Asset } from "@/lib/inventory";

/** The asset list for the order forms, with its own loading and error state. */
export function useAssets() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setAssets(await getProducts());
    } catch (reason) {
      setError(getUserMessage(reason));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Fetching on mount is the point of this effect; load() flags "loading" first.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  return { assets, loading, error, reload: load };
}
