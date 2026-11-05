"use client";

import { AlertTriangle, FileDown, Loader2, Search, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import type { Instance } from "@/lib/datajud";
import {
  daysBetween, describeMovement, humanDuration, milestoneOf, parseDatajudDate, redistributions, type Milestone,
} from "@/lib/movements";

const STALE_DAYS = 90; // sem movimentação há mais que isso, e sem baixa: vale olhar
const lastMove = (p: Instance) => parseDatajudDate(p.movements[0]?.date ?? null)?.getTime() ?? 0;

/** `moved`: outra instância do mesmo processo movimentou depois desta (ex.: subiu para a Turma Recursal). */
function InstanceCard({ p, moved }: { p: Instance; moved: boolean }) {
  const [onlyMilestones, setOnlyMilestones] = useState(false);
  const now = new Date();
  const moves = p.movements.map((m) => ({ ...m, milestone: milestoneOf(m.name, m.code) }));
  const filed = parseDatajudDate(p.filedAt);
  const last = parseDatajudDate(moves[0]?.date ?? null);
  const idle = last ? daysBetween(last, now) : null;
  // Encerramento mais recente (a lista vem da mais nova para a mais antiga)
  const closing = moves.find((m) => m.milestone === "Baixa / arquivamento" || m.milestone === "Trânsito em julgado");
  const closed = !!closing;
  const stale = idle !== null && idle > STALE_DAYS && !closed && !moved;
  // O órgão do cabeçalho do Datajud pode estar desatualizado; o da última movimentação é o atual
  const currentBody = moves.find((m) => m.body)?.body ?? p.body;
  const redists = redistributions(moves);
  const after = closing && moves[0] !== closing ? moves[0] : null; // houve movimentação depois do arquivamento
  const situation = closing
    ? `${closing.milestone === "Trânsito em julgado" ? "Trânsito em julgado" : "Arquivado / baixado"} em ${fmtDate(closing.date)}`
    : moved ? "Remetido a outra instância" : "Em andamento";
  // Data mais recente de cada marco (a lista já vem da mais nova para a mais antiga)
  const milestones = new Map<Milestone, string>();
  for (const m of moves) if (m.milestone && !milestones.has(m.milestone)) milestones.set(m.milestone, m.date);
  const shown = onlyMilestones ? moves.filter((m) => m.milestone) : moves;

  return (
    <article className="rounded-xl border border-line bg-card p-5 text-sm">
      <header className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h4 className="font-display text-base font-semibold">{p.className || "Classe não informada"}</h4>
        <span className="text-muted">{p.court} · {p.degree}</span>
      </header>

      <div className="mb-4 grid gap-3 sm:grid-cols-3">
        <Stat label="Tramitando há" value={filed ? humanDuration(daysBetween(filed, now)) : "—"} />
        <Stat label="Última movimentação" value={idle !== null ? `há ${humanDuration(idle)}` : "—"} warn={stale} />
        <Stat label="Situação" value={situation} />
      </div>
      {stale && (
        <p className="mb-4 flex items-center gap-2 rounded-lg bg-surface p-2 text-gold">
          <AlertTriangle className="size-4 shrink-0" aria-hidden /> Sem movimentação há mais de {STALE_DAYS} dias.
        </p>
      )}
      {after && (
        <p className="mb-4 rounded-lg bg-surface p-2 text-muted">
          Houve movimentação depois do encerramento ({describeMovement(after)}, em {fmtDate(after.date)}); confira se houve desarquivamento.
        </p>
      )}

      <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-[9rem_1fr]">
        <dt className="text-muted">Órgão julgador atual</dt><dd>{currentBody || "—"}</dd>
        {redists.length > 0 && (
          <>
            <dt className="text-muted">Redistribuições</dt>
            <dd>{redists.map((r) => `${fmtDate(r.date)}: de ${r.from} para ${r.to}`).join("; ")}</dd>
          </>
        )}
        <dt className="text-muted">Assuntos</dt><dd>{p.subjects.join(" · ") || "—"}</dd>
        <dt className="text-muted">Ajuizamento</dt><dd>{fmtDate(p.filedAt)}</dd>
        <dt className="text-muted">Sistema</dt><dd>{p.system ?? "—"}</dd>
      </dl>

      {milestones.size > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {[...milestones].map(([name, date]) => (
            <span key={name} className="rounded-full bg-accent/10 px-2.5 py-1 text-xs text-accent">
              <strong>{name}</strong> · {fmtDate(date)}
            </span>
          ))}
        </div>
      )}

      {moves.length > 0 && (
        <details className="mt-4">
          <summary className="cursor-pointer text-muted">Linha do tempo ({moves.length} movimentações)</summary>
          <label className="mt-2 flex items-center gap-2 text-muted">
            <input type="checkbox" checked={onlyMilestones} onChange={(e) => setOnlyMilestones(e.target.checked)} />
            Só marcos processuais
          </label>
          <ol className="mt-2 space-y-1 border-l-2 border-line pl-3">
            {shown.map((m, k) => (
              <li key={k} className="grid grid-cols-[6.5rem_1fr] gap-2">
                <span className="tabular-nums text-muted">{fmtDate(m.date)}</span>
                <span>
                  <span className={m.milestone ? "font-semibold" : undefined}>{describeMovement(m)}</span>
                  {m.body && m.body !== currentBody && <span className="text-muted"> · {m.body}</span>}
                </span>
              </li>
            ))}
          </ol>
        </details>
      )}
    </article>
  );
}

function Stat({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="rounded-lg bg-surface p-3">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-1 font-semibold ${warn ? "text-gold" : ""}`}>{value}</p>
    </div>
  );
}

type State =
  | { status: "idle" }
  | { status: "busy" }
  | { status: "done"; numero: string; instances: Instance[] }
  | { status: "error"; msg: string; limited?: boolean };

// Limite de consultas (429), lentidão (504) e instabilidade (502) do Datajud: o caminho é analisar os autos em PDF
const LIMITED = new Set([429, 502, 504]);

/** Leva até a área de envio de PDFs (id="enviar" no analisador) e abre a escolha de arquivos. */
function goToUpload() {
  const area = document.getElementById("enviar");
  area?.scrollIntoView({ behavior: "smooth", block: "center" });
  area?.querySelector<HTMLInputElement>("input[type=file]")?.click();
}

const fmtDate = (iso: string | null) => parseDatajudDate(iso)?.toLocaleDateString("pt-BR", { timeZone: "UTC" }) ?? "—";

async function lookup(numero: string): Promise<State> {
  try {
    const res = await fetch("/api/processo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ numero }),
    });
    const data = (await res.json()) as { error?: string; numero?: string; instances?: Instance[] };
    if (!res.ok || !data.instances) {
      return { status: "error", msg: data.error ?? "Erro inesperado na consulta.", limited: LIMITED.has(res.status) };
    }
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

/**
 * `initial` vem de um número CNJ encontrado no documento; a consulta dispara sozinha.
 * `onResult` entrega o andamento ao analisador para entrar no relatório em PDF.
 */
export function ProcessLookup({ initial = "", onResult, onReport }: {
  initial?: string;
  onResult: (numero: string, instances: Instance[]) => void;
  onReport: (numero: string) => void;
}) {
  const [value, setValue] = useState(initial);
  const [state, setState] = useState<State>(initial ? { status: "busy" } : { status: "idle" });

  const finish = (s: State) => {
    setState(s);
    if (s.status === "done") onResult(s.numero, s.instances);
  };

  useEffect(() => {
    if (initial) lookup(initial).then(finish);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- consulta só quando o número pedido muda
  }, [initial]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState({ status: "busy" });
    finish(await lookup(value));
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
          <div role="alert" className="rounded-lg border border-line bg-surface p-3 text-sm">
            <p className={state.limited ? "font-semibold text-gold" : undefined}>{state.msg}</p>
            {state.limited && (
              <>
                <p className="mt-2">
                  O melhor caminho é baixar os autos manualmente no sistema do tribunal (PJe, eproc, e-SAJ, Projudi…) e
                  adicionar os PDFs aqui no S.A.P.O. para a varredura completa: partes, dispositivo, prazos, valores e
                  relatório em PDF, tudo processado no seu navegador.
                </p>
                <button type="button" onClick={goToUpload}
                  className="mt-3 inline-flex items-center gap-2 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-on-accent">
                  <Upload className="size-4" aria-hidden /> Adicionar os autos em PDF
                </button>
              </>
            )}
          </div>
        )}
        {state.status === "done" && (
          <div className="space-y-4">
            {state.instances.map((p, i) => (
              <InstanceCard key={i} p={p}
                moved={state.instances.some((o) => lastMove(o) > lastMove(p))} />
            ))}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs text-muted">
                Fonte: API Pública do Datajud (CNJ). Atualizado em {fmtDate(state.instances[0].updatedAt)}.
              </p>
              <button type="button" onClick={() => onReport(state.numero)}
                className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm hover:bg-surface">
                <FileDown className="size-4" aria-hidden /> Relatório do andamento (PDF)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
