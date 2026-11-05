"use client";

import { Download, FileText, Search, ShieldCheck } from "lucide-react";
import type { Analysis } from "@/lib/analyze";
import { isPersonal, type EntityType } from "@/lib/ner";
import { CaseSheet } from "./case-sheet";

const ENTITY_LABEL: Record<EntityType, string> = {
  CPF: "CPF", CNPJ: "CNPJ", RG: "RG", CNH: "CNH", PIS: "PIS/NIS", EMAIL: "E-mail", TELEFONE: "Telefone",
  ENDERECO: "Endereço", CEP: "CEP", PLACA: "Placa", PROCESSO_CNJ: "Processo (CNJ)", OAB: "OAB", DATA: "Data",
  VALOR: "Valor", LEI: "Lei", ARTIGO: "Artigo", TRIBUNAL: "Tribunal", SUMULA: "Súmula", RECURSO: "Recurso",
};

export function Result({ result, name, onLookup }: { result: Analysis; name: string; onLookup: (numero: string) => void }) {
  const personal = result.entities.filter((e) => isPersonal(e.type));
  const legal = result.entities.filter((e) => !isPersonal(e.type) && e.type !== "PROCESSO_CNJ");

  function download() {
    const url = URL.createObjectURL(new Blob([result.anonymized], { type: "text/plain;charset=utf-8" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `${name.replace(/\.pdf$/i, "")}-anonimizado.txt` });
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="space-y-4" aria-label="Resultado da análise">
      <p className="flex items-center gap-2 text-sm text-muted">
        <FileText className="size-4" aria-hidden />
        {name} · {result.pages} {result.pages === 1 ? "página" : "páginas"}
        {result.ocrPages > 0 && ` · ${result.ocrPages} com OCR`} · análise em {result.ms.toFixed(0)} ms, no seu navegador
      </p>

      <CaseSheet result={result} onLookup={onLookup} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Resumo extrativo">
          {result.summary.length ? (
            <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed">
              {result.summary.map((s) => <li key={s}>{s}</li>)}
            </ol>
          ) : <p className="text-sm text-muted">Texto curto demais para resumir.</p>}
        </Card>

        <Card title="Tipo de documento">
          <ul className="space-y-2">
            {result.ranking.map((p, i) => (
              <li key={p.label} className="grid grid-cols-[7.5rem_1fr_3rem] items-center gap-3 text-sm">
                <span className={i === 0 ? "font-semibold" : "text-muted"}>{p.label}</span>
                <span className="h-2 overflow-hidden rounded-full bg-line">
                  <span className={`block h-full rounded-full ${i === 0 ? "bg-accent" : "bg-muted/50"}`} style={{ width: `${p.probability * 100}%` }} />
                </span>
                <span className="text-right tabular-nums text-muted">{(p.probability * 100).toFixed(0)}%</span>
              </li>
            ))}
          </ul>
          {result.segments.length > 1 && (
            <div className="mt-5">
              <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Peças identificadas</h4>
              <ol className="space-y-1 text-sm">
                {result.segments.map((s) => (
                  <li key={s.from}>
                    <span className="tabular-nums text-muted">{s.from === s.to ? `p. ${s.from}` : `pp. ${s.from}–${s.to}`}</span> · {s.label}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </Card>

        <Card title="Dados pessoais (LGPD)">
          <div className="mb-4 flex items-baseline gap-3">
            <span className="text-3xl font-semibold tabular-nums">{result.exposure.score}</span>
            <span className="text-sm text-muted">/ 100 · exposição {result.exposure.level.toLowerCase()}</span>
          </div>
          {personal.length === 0 ? (
            <p className="flex items-center gap-2 text-sm text-muted"><ShieldCheck className="size-4" aria-hidden /> Nenhum dado pessoal identificado.</p>
          ) : (
            <>
              <EntityList entities={personal} />
              <button type="button" onClick={download}
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium hover:bg-surface print:hidden">
                <Download className="size-4" aria-hidden /> Baixar texto anonimizado
              </button>
            </>
          )}
        </Card>

        <Card title="Referências jurídicas">
          {legal.length ? <EntityList entities={legal} onLookup={onLookup} /> : <p className="text-sm text-muted">Nenhuma referência encontrada.</p>}
        </Card>
      </div>
    </section>
  );
}

function EntityList({ entities, onLookup }: { entities: Analysis["entities"]; onLookup?: (numero: string) => void }) {
  const groups = Map.groupBy(entities, (e) => e.type);
  return (
    <dl className="space-y-2 text-sm">
      {[...groups].map(([type, list]) => (
        <div key={type} className="grid grid-cols-[7.5rem_1fr] gap-3">
          <dt className="text-muted">{ENTITY_LABEL[type]}</dt>
          <dd className="flex flex-wrap gap-1.5">
            {[...new Set(list.map((e) => e.value))].slice(0, 12).map((v) =>
              type === "PROCESSO_CNJ" && onLookup ? (
                <button key={v} type="button" onClick={() => onLookup(v)} title="Consultar no Datajud"
                  className="inline-flex items-center gap-1 rounded bg-surface px-1.5 py-0.5 font-mono text-xs text-accent underline-offset-2 hover:underline">
                  {v} <Search className="size-3" aria-hidden />
                </button>
              ) : (
                <code key={v} className="rounded bg-surface px-1.5 py-0.5 text-xs">{v}</code>
              ),
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="break-inside-avoid rounded-xl border border-line bg-card p-5">
      <h3 className="mb-4 font-display text-lg font-semibold">{title}</h3>
      {children}
    </div>
  );
}
