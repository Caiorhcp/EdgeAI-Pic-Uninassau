"use client";

import { Loader2, Search } from "lucide-react";
import { useEffect, useState } from "react";
import type { Instance } from "@/lib/datajud";

type State =
  | { status: "idle" }
  | { status: "busy" }
  | { status: "done"; numero: string; instances: Instance[] }
  | { status: "error"; msg: string };

const fmtDate = (iso: string | null) => {
  if (!iso) return "—";
  // Datajud usa ISO ("2024-03-14T10:00:00.000Z") ou compacto ("20240314100000")
  const d = /^\d{14}$/.test(iso) ? new Date(`${iso.slice(0, 4)}-${iso.slice(4, 6)}-${iso.slice(6, 8)}T00:00:00`) : new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("pt-BR");
};

async function lookup(numero: string): Promise<State> {
  try {
    const res = await fetch("/api/processo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ numero }),
    });
    const data = (await res.json()) as { error?: string; numero?: string; instances?: Instance[] };
    if (!res.ok || !data.instances) return { status: "error", msg: data.error ?? "Erro inesperado na consulta." };
    return { status: "done", numero: data.numero!, instances: data.instances };
  } catch {
    return {
      status: "error",
      msg: navigator.onLine
        ? "Sem conexão com o servidor."
        : "Você está offline. A análise de documentos funciona sem internet, mas a consulta ao Datajud precisa de conexão.",
    };
  }
}

/** `initial` vem de um número CNJ encontrado no documento; a consulta dispara sozinha. */
export function ProcessLookup({ initial = "" }: { initial?: string }) {
  const [value, setValue] = useState(initial);
  const [state, setState] = useState<State>(initial ? { status: "busy" } : { status: "idle" });

  useEffect(() => {
    if (initial) lookup(initial).then(setState);
  }, [initial]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState({ status: "busy" });
    setState(await lookup(value));
  }

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="flex flex-wrap gap-2">
        <label htmlFor="cnj" className="sr-only">Número do processo (CNJ)</label>
        <input id="cnj" value={value} onChange={(e) => setValue(e.target.value)} inputMode="numeric"
          placeholder="0000000-00.0000.0.00.0000"
          className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-2 font-mono text-sm outline-none focus:border-accent" />
        <button type="submit" disabled={state.status === "busy" || !value.trim()}
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-on-accent disabled:opacity-40">
          {state.status === "busy" ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Search className="size-4" aria-hidden />}
          Consultar
        </button>
      </form>

      <div aria-live="polite">
        {state.status === "busy" && (
          <p className="text-sm text-muted">Consultando o Datajud. A API do CNJ costuma levar até um minuto…</p>
        )}
        {state.status === "error" && (
          <p role="alert" className="rounded-lg border border-line bg-surface p-3 text-sm">{state.msg}</p>
        )}
        {state.status === "done" && (
          <div className="space-y-4">
            {state.instances.map((p, i) => (
              <article key={i} className="rounded-xl border border-line bg-card p-5 text-sm">
                <header className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                  <h4 className="font-semibold">{p.className || "Classe não informada"}</h4>
                  <span className="text-muted">{p.court} · {p.degree}</span>
                </header>
                <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-[8rem_1fr]">
                  <dt className="text-muted">Órgão julgador</dt><dd>{p.body || "—"}</dd>
                  <dt className="text-muted">Assuntos</dt><dd>{p.subjects.join(" · ") || "—"}</dd>
                  <dt className="text-muted">Ajuizamento</dt><dd>{fmtDate(p.filedAt)}</dd>
                  <dt className="text-muted">Sistema</dt><dd>{p.system ?? "—"}</dd>
                </dl>
                {p.movements.length > 0 && (
                  <details className="mt-4">
                    <summary className="cursor-pointer text-muted">Últimas movimentações ({p.movements.length})</summary>
                    <ol className="mt-2 space-y-1">
                      {p.movements.map((m, k) => (
                        <li key={k} className="grid grid-cols-[6.5rem_1fr] gap-2">
                          <span className="tabular-nums text-muted">{fmtDate(m.date)}</span><span>{m.name}</span>
                        </li>
                      ))}
                    </ol>
                  </details>
                )}
              </article>
            ))}
            <p className="text-xs text-muted">
              Fonte: API Pública do Datajud (CNJ). Atualizado em {fmtDate(state.instances[0].updatedAt)}.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
