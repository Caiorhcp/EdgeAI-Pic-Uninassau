"use client";

import { CalendarClock, Gavel, Search, Users } from "lucide-react";
import { useState } from "react";
import type { Analysis } from "@/lib/analyze";
import { courtOf } from "@/lib/cnj";
import { dueDate } from "@/lib/deadlines";

const fmt = (iso: string) => new Date(`${iso}T00:00:00Z`).toLocaleDateString("pt-BR", { timeZone: "UTC" });
const todayIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

/** Ficha com o que o profissional precisa ver primeiro: o que é, quem são, o que foi decidido, prazos e valores. */
export function CaseSheet({ result, onLookup }: { result: Analysis; onLookup: (numero: string) => void }) {
  const [intimation, setIntimation] = useState(todayIso);
  const own = result.outcomes.filter((o) => o.own);
  const cited = result.outcomes.filter((o) => !o.own);
  const active = result.parties.filter((p) => p.side === "ativo");
  const passive = result.parties.filter((p) => p.side === "passivo");

  return (
    <div className="rounded-xl border-2 border-accent/40 bg-card p-5">
      <h3 className="mb-4 font-display text-xl font-semibold">Ficha do processo</h3>

      <dl className="grid gap-x-8 gap-y-4 text-sm md:grid-cols-2">
        <Field label="Tipo provável">
          <span className="font-semibold">{result.ranking[0].label}</span>{" "}
          <span className="text-muted">({(result.ranking[0].probability * 100).toFixed(0)}%)</span>
        </Field>

        <Field label="Processo">
          {result.processNumbers.length ? (
            <span className="flex flex-wrap gap-1.5">
              {result.processNumbers.map((n) => (
                <span key={n} className="inline-flex items-center gap-1.5">
                  <button type="button" onClick={() => onLookup(n)} title="Consultar no Datajud"
                    className="inline-flex items-center gap-1 rounded bg-surface px-1.5 py-0.5 font-mono text-xs text-accent hover:underline">
                    {n} <Search className="size-3" aria-hidden />
                  </button>
                  {/* Tribunal pelos segmentos J.TR do próprio número (Res. CNJ 65/2008), não pelos tribunais citados no texto */}
                  <span className="text-muted">{courtOf(n) ?? "número com dígito verificador inválido"}</span>
                </span>
              ))}
            </span>
          ) : <Empty />}
        </Field>

        <Field label="Resultado" icon={<Gavel className="size-4" aria-hidden />}>
          {own.length ? (
            <ul className="space-y-1">
              {own.map((o, i) => <li key={i}><Badge>{o.label}</Badge> <Quote text={o.excerpt} /></li>)}
            </ul>
          ) : <span className="text-muted">Nenhum dispositivo nesta peça.</span>}
          {cited.length > 0 && (
            <p className="mt-2 text-muted">
              Decisões citadas: {[...new Set(cited.map((o) => o.label))].join(", ")}
            </p>
          )}
        </Field>

        <Field label="Partes" icon={<Users className="size-4" aria-hidden />}>
          {result.parties.length ? (
            <div className="space-y-1">
              {active.length > 0 && <p><span className="text-muted">Polo ativo:</span> {active.map((p) => `${p.name} (${p.role})`).join("; ")}</p>}
              {passive.length > 0 && <p><span className="text-muted">Polo passivo:</span> {passive.map((p) => `${p.name} (${p.role})`).join("; ")}</p>}
              {result.lawyers.length > 0 && (
                <p><span className="text-muted">Advogados:</span> {result.lawyers.map((l) => (l.name ? `${l.name}, ${l.oab}` : l.oab)).join("; ")}</p>
              )}
            </div>
          ) : <Empty />}
        </Field>

        <Field label="Prazos" icon={<CalendarClock className="size-4" aria-hidden />} wide>
          {result.deadlines.length ? (
            <>
              <label className="mb-2 flex flex-wrap items-center gap-2 text-muted print:hidden">
                Intimação ou ciência em
                <input type="date" value={intimation} onChange={(e) => setIntimation(e.target.value)}
                  className="rounded border border-line bg-surface px-2 py-1 text-foreground" />
              </label>
              <ul className="space-y-2">
                {result.deadlines.map((d, i) => {
                  const due = intimation ? dueDate(intimation, d) : null;
                  return (
                    <li key={i} className="grid gap-1 sm:grid-cols-[11rem_1fr] sm:gap-3">
                      <span>
                        <Badge>{d.amount} {d.unit}{d.unit === "dias" ? (d.businessDays ? " úteis" : " corridos") : ""}</Badge>
                        {due && <span className="ml-2 font-semibold text-gold">vence {fmt(due.toISOString().slice(0, 10))}</span>}
                      </span>
                      <Quote text={d.excerpt} />
                    </li>
                  );
                })}
              </ul>
              <p className="mt-2 text-xs text-muted">
                Estimativa pelo CPC (arts. 219, 220 e 224) com feriados nacionais e recesso. Não inclui feriados locais nem
                regras especiais de intimação; confira no sistema do tribunal.
              </p>
            </>
          ) : <span className="text-muted">Nenhum prazo encontrado no texto.</span>}
        </Field>

        <Field label="Valores">
          {result.values.length ? (
            <ul className="space-y-1">
              {result.values.map((v, i) => <li key={i}><span className="text-muted">{v.label}:</span> <span className="tabular-nums">{v.value}</span></li>)}
            </ul>
          ) : <Empty />}
        </Field>

        <Field label="Linha do tempo">
          {result.events.length ? (
            <ol className="space-y-1">
              {result.events.map((e, i) => (
                <li key={i} className="grid grid-cols-[5.5rem_1fr] gap-2">
                  <span className="tabular-nums text-muted">{fmt(e.date)}</span><Quote text={e.excerpt} />
                </li>
              ))}
            </ol>
          ) : <Empty />}
        </Field>
      </dl>
    </div>
  );
}

function Field({ label, icon, wide, children }: { label: string; icon?: React.ReactNode; wide?: boolean; children: React.ReactNode }) {
  return (
    <div className={wide ? "md:col-span-2" : undefined}>
      <dt className="mb-1 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted">{icon}{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

const Badge = ({ children }: { children: React.ReactNode }) => (
  <span className="inline-block rounded bg-accent/10 px-1.5 py-0.5 text-xs font-semibold text-accent">{children}</span>
);
const Quote = ({ text }: { text: string }) => <span className="text-muted">“{text}”</span>;
const Empty = () => <span className="text-muted">Não identificado.</span>;
