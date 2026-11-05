"use client";

import { CalendarClock, Gavel, Landmark, Scale, Search, Users } from "lucide-react";
import type { Analysis } from "@/lib/analyze";
import { courtOf } from "@/lib/cnj";
import { dueDate } from "@/lib/deadlines";
import { CourtLink } from "./court-link";

export const fmtIso = (iso: string) => new Date(`${iso}T00:00:00Z`).toLocaleDateString("pt-BR", { timeZone: "UTC" });

/** Ficha com o que o profissional precisa ver primeiro, em linguagem dos autos. */
export function CaseSheet({ result, intimation, onIntimation, onLookup }: {
  result: Analysis;
  intimation: string;
  onIntimation: (iso: string) => void;
  onLookup: (numero: string) => void;
}) {
  const own = result.outcomes.filter((o) => o.own);
  const cited = result.outcomes.filter((o) => !o.own);
  const active = result.parties.filter((p) => p.side === "ativo");
  const passive = result.parties.filter((p) => p.side === "passivo");
  const { header } = result;

  return (
    <div className="rounded-xl border-2 border-accent/40 bg-card p-5">
      <h3 className="mb-4 font-display text-xl font-semibold">Ficha do processo</h3>

      <dl className="grid gap-x-8 gap-y-5 text-sm md:grid-cols-2">
        <Field label="Identificação" icon={<Landmark className="size-4" aria-hidden />}>
          <Row k="Natureza da peça">
            <strong>{result.ranking[0].label}</strong>{" "}
            <span className="text-muted">(classificação automática, {(result.ranking[0].probability * 100).toFixed(0)}%)</span>
          </Row>
          <Row k="Autos nº">
            {result.processNumbers.length ? (
              <span className="flex flex-wrap gap-1.5">
                {result.processNumbers.map((n) => (
                  <span key={n} className="inline-flex items-center gap-1.5">
                    <button type="button" onClick={() => onLookup(n)} title="Consultar andamento no Datajud"
                      className="inline-flex items-center gap-1 rounded bg-surface px-1.5 py-0.5 font-mono text-xs text-accent hover:underline">
                      {n} <Search className="size-3" aria-hidden />
                    </button>
                    {/* Tribunal pelos segmentos J.TR do número (Res. CNJ 65/2008), não pelos tribunais citados */}
                    <span className="text-muted">{courtOf(n) ?? "dígito verificador inválido"}</span>
                    <CourtLink numero={n} compact />
                  </span>
                ))}
              </span>
            ) : "não identificado"}
          </Row>
          <Row k="Juízo / órgão julgador">{header.body ?? "não identificado"}</Row>
          {header.district && <Row k="Comarca">{header.district}</Row>}
          {header.judge && <Row k="Magistrado(a) / relator(a)">{header.judge}</Row>}
          {header.action && <Row k="Natureza da ação">{header.action}</Row>}
        </Field>

        <Field label="Partes e procuradores" icon={<Users className="size-4" aria-hidden />}>
          <Row k="Polo ativo">{active.length ? active.map((p) => `${p.name} (${p.role.toLowerCase()})`).join("; ") : "não identificado"}</Row>
          <Row k="Polo passivo">{passive.length ? passive.map((p) => `${p.name} (${p.role.toLowerCase()})`).join("; ") : "não identificado"}</Row>
          <Row k="Procuradores">
            {result.lawyers.length ? result.lawyers.map((l) => (l.name ? `${l.name}, ${l.oab}` : l.oab)).join("; ") : "não identificados"}
          </Row>
        </Field>

        <Field label="Dispositivo" icon={<Gavel className="size-4" aria-hidden />} wide>
          {own.length ? (
            <ul className="space-y-1.5">
              {own.map((o, i) => <li key={i}><Badge>{o.label}</Badge> <Quote text={o.excerpt} /></li>)}
            </ul>
          ) : <p className="text-muted">A peça não contém dispositivo decisório (ato de parte ou ato ordinatório).</p>}
          {cited.length > 0 && (
            <div className="mt-3">
              <p className="mb-1 text-muted">Decisões anteriores mencionadas:</p>
              <ul className="space-y-1">
                {cited.map((o, i) => <li key={i}><Badge>{o.label}</Badge> <Quote text={o.excerpt} /></li>)}
              </ul>
            </div>
          )}
        </Field>

        {result.requests.length > 0 && (
          <Field label="Pedidos formulados" wide>
            <ul className="list-disc space-y-1 pl-5">{result.requests.map((r, i) => <li key={i}>{r}</li>)}</ul>
          </Field>
        )}

        <Field label="Prazos processuais" icon={<CalendarClock className="size-4" aria-hidden />} wide>
          {result.deadlines.length ? (
            <>
              <label className="mb-3 flex flex-wrap items-center gap-2 text-muted">
                Termo inicial (intimação ou ciência):
                <input type="date" value={intimation} onChange={(e) => onIntimation(e.target.value)}
                  className="rounded border border-line bg-surface px-2 py-1 text-foreground" />
              </label>
              <ul className="space-y-2">
                {result.deadlines.map((d, i) => {
                  const due = intimation ? dueDate(intimation, d) : null;
                  return (
                    <li key={i} className="grid gap-1 sm:grid-cols-[13rem_1fr] sm:gap-3">
                      <span>
                        <Badge>{d.amount} {d.unit}{d.unit === "dias" ? (d.businessDays ? " úteis" : " corridos") : ""}</Badge>
                        <span className="ml-2 font-semibold text-gold">
                          {due ? `termo final ${fmtIso(due.toISOString().slice(0, 10))}` : d.unit === "horas" ? "contar da hora da intimação" : ""}
                        </span>
                      </span>
                      <Quote text={d.excerpt} />
                    </li>
                  );
                })}
              </ul>
              <p className="mt-2 text-xs text-muted">
                Contagem estimada nos termos dos arts. 219, 220 e 224 do CPC, considerados feriados nacionais e o recesso forense.
                Não abrange feriados locais, suspensões determinadas pelo tribunal nem as regras do art. 231 do CPC.
              </p>
            </>
          ) : <p className="text-muted">Nenhum prazo assinalado no texto.</p>}
        </Field>

        <Field label="Valores" icon={<Scale className="size-4" aria-hidden />}>
          {result.values.length ? (
            <ul className="space-y-1">
              {result.values.map((v, i) => <li key={i}><span className="text-muted">{v.label}:</span> <span className="tabular-nums">{v.value}</span></li>)}
            </ul>
          ) : <p className="text-muted">Nenhum valor mencionado.</p>}
        </Field>

        <Field label="Fundamentação normativa citada">
          {result.laws.laws.length + result.laws.articles.length + result.laws.precedents.length ? (
            <div className="space-y-1">
              {result.laws.laws.length > 0 && <Row k="Diplomas">{result.laws.laws.join("; ")}</Row>}
              {result.laws.articles.length > 0 && <Row k="Dispositivos">{result.laws.articles.join("; ")}</Row>}
              {result.laws.precedents.length > 0 && <Row k="Súmulas e precedentes">{result.laws.precedents.join("; ")}</Row>}
            </div>
          ) : <p className="text-muted">Nenhuma norma identificada.</p>}
        </Field>

        <Field label="Cronologia" wide>
          {result.events.length ? (
            <ol className="space-y-1">
              {result.events.map((e, i) => (
                <li key={i} className="grid grid-cols-[5.5rem_1fr] gap-2">
                  <span className="tabular-nums text-muted">{fmtIso(e.date)}</span><Quote text={e.excerpt} />
                </li>
              ))}
            </ol>
          ) : <p className="text-muted">Nenhuma data identificada.</p>}
        </Field>
      </dl>
    </div>
  );
}

function Field({ label, icon, wide, children }: { label: string; icon?: React.ReactNode; wide?: boolean; children: React.ReactNode }) {
  return (
    <div className={wide ? "md:col-span-2" : undefined}>
      <dt className="mb-2 flex items-center gap-1.5 border-b border-line pb-1 text-xs font-medium uppercase tracking-wide text-muted">{icon}{label}</dt>
      <dd className="space-y-1">{children}</dd>
    </div>
  );
}

const Row = ({ k, children }: { k: string; children: React.ReactNode }) => (
  <p><span className="text-muted">{k}:</span> {children}</p>
);
const Badge = ({ children }: { children: React.ReactNode }) => (
  <span className="inline-block rounded bg-accent/10 px-1.5 py-0.5 text-xs font-semibold text-accent">{children}</span>
);
const Quote = ({ text }: { text: string }) => <span className="text-muted">“{text}”</span>;
