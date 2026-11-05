"use client";

import { CloudOff, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

type Status = "idle" | "preparing" | "ready" | "unsupported";

export function OfflineStatus() {
  const [status, setStatus] = useState<Status>("idle");

  useEffect(() => {
    // Em desenvolvimento o service worker atrapalharia o recarregamento automático
    if (process.env.NODE_ENV !== "production") return;
    const id = setTimeout(() => {
      setStatus("preparing");
      import("@/lib/offline")
        .then((m) => m.prepareOffline())
        .then((ok) => setStatus(ok ? "ready" : "unsupported"))
        .catch(() => setStatus("unsupported"));
    }, 1500); // deixa a página terminar de carregar antes de baixar o resto
    return () => clearTimeout(id);
  }, []);

  if (status === "idle" || status === "unsupported") return null;
  return (
    <p className="inline-flex items-center gap-2 rounded-full border border-line px-3 py-1 text-xs text-muted" aria-live="polite">
      {status === "preparing" ? (
        <><Loader2 className="size-3.5 animate-spin" aria-hidden /> Preparando uso offline…</>
      ) : (
        <><CloudOff className="size-3.5" aria-hidden /> Pronto para uso offline</>
      )}
    </p>
  );
}
