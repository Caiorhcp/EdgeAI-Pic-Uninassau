"use client";

import { Download, FileText, Loader2, ShieldCheck, Upload } from "lucide-react";
import { useState } from "react";
import { analyze, loadClassifier, type Analysis } from "@/lib/analyze";
import { isPersonal, type EntityType } from "@/lib/ner";
import type { Page } from "@/lib/pdf";
import { EXAMPLE_PAGES } from "./example";

type State = { status: "idle" } | { status: "busy"; msg: string } | { status: "done"; result: Analysis; name: string } | { status: "error"; msg: string };

const ENTITY_LABEL: Record<EntityType, string> = {
  CPF: "CPF", CNPJ: "CNPJ", RG: "RG", CNH: "CNH", PIS: "PIS/NIS", EMAIL: "E-mail", TELEFONE: "Telefone",
  ENDERECO: "Endereço", CEP: "CEP", PLACA: "Placa", PROCESSO_CNJ: "Processo (CNJ)", OAB: "OAB", DATA: "Data",
  VALOR: "Valor", LEI: "Lei", ARTIGO: "Artigo", TRIBUNAL: "Tribunal", SUMULA: "Súmula", RECURSO: "Recurso",
};

export function Analyzer() {
  const [state, setState] = useState<State>({ status: "idle" });
  const [text, setText] = useState("");
  const [dragging, setDragging] = useState(false);

  async function run(name: string, getPages: (progress: (m: string) => void) => Promise<Page[]>) {
    try {
      setState({ status: "busy", msg: "Carregando modelo" });
      const clf = await loadClassifier();
      const pages = await getPages((msg) => setState({ status: "busy", msg }));
      if (!pages.some((p) => p.text.trim())) throw new Error("Não foi possível extrair texto deste documento.");
      setState({ status: "done", result: analyze(clf, pages), name });
    } catch (e) {
      setState({ status: "error", msg: e instanceof Error ? e.message : "Erro inesperado." });
    }
  }

  function onFile(file: File | undefined) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setState({ status: "error", msg: "Envie um arquivo PDF." });
      return;
    }
    run(file.name, async (progress) => (await import("@/lib/pdf")).readPdf(file, progress));
  }

  const busy = state.status === "busy";

  return (
    <div className="space-y-8">
      <section className="grid gap-4 md:grid-cols-2">
        <label
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); onFile(e.dataTransfer.files[0]); }}
          className={`flex min-h-48 cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-6 text-center transition ${dragging ? "border-accent bg-accent/5" : "border-line hover:border-accent/60"}`}
        >
          <Upload className="size-8 text-muted" aria-hidden />
          <span className="font-medium">Arraste um PDF ou clique para escolher</span>
          <span className="text-sm text-muted">PDFs digitais ou escaneados (OCR automático), até 200 páginas</span>
          <input type="file" accept="application/pdf" className="sr-only" disabled={busy}
            onChange={(e) => { onFile(e.target.files?.[0]); e.target.value = ""; }} />
        </label>

        <div className="flex flex-col gap-3">
          <label htmlFor="texto" className="sr-only">Texto do documento</label>
          <textarea id="texto" value={text} onChange={(e) => setText(e.target.value)} disabled={busy}
            placeholder="…ou cole o texto de uma peça processual aqui"
            className="min-h-36 flex-1 resize-y rounded-xl border border-line bg-surface p-4 text-sm outline-none focus:border-accent" />
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={busy || !text.trim()}
              onClick={() => run("Texto colado", async () => [{ number: 1, text, ocr: false }])}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
              Analisar texto
            </button>
            <button type="button" disabled={busy} onClick={() => run("Exemplo", async () => EXAMPLE_PAGES)}
              className="rounded-lg border border-line px-4 py-2 text-sm font-medium hover:bg-surface disabled:opacity-40">
              Usar documento de exemplo
            </button>
          </div>
        </div>
      </section>

      <div aria-live="polite">
        {state.status === "busy" && (
          <p className="flex items-center gap-2 text-sm text-muted">
            <Loader2 className="size-4 animate-spin" aria-hidden /> {state.msg}…
          </p>
        )}
        {state.status === "error" && (
          <p role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
            {state.msg}
          </p>
        )}
      </div>

      {state.status === "done" && <Result result={state.result} name={state.name} />}
    </div>
  );
}

function Result({ result, name }: { result: Analysis; name: string }) {
  const personal = result.entities.filter((e) => isPersonal(e.type));
  const legal = result.entities.filter((e) => !isPersonal(e.type));
  const pages = result.segments.at(-1)?.to ?? 1;

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
        {name} · {pages} {pages === 1 ? "página" : "páginas"}
        {result.ocrPages > 0 && ` · ${result.ocrPages} com OCR`} · análise em {result.ms.toFixed(0)} ms, no seu navegador
      </p>

      <div className="grid gap-4 lg:grid-cols-2">
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
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium hover:bg-surface">
                <Download className="size-4" aria-hidden /> Baixar texto anonimizado
              </button>
            </>
          )}
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Resumo extrativo">
          {result.summary.length ? (
            <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed">
              {result.summary.map((s) => <li key={s}>{s}</li>)}
            </ol>
          ) : <p className="text-sm text-muted">Texto curto demais para resumir.</p>}
        </Card>
        <Card title="Referências jurídicas">
          {legal.length ? <EntityList entities={legal} /> : <p className="text-sm text-muted">Nenhuma referência encontrada.</p>}
        </Card>
      </div>
    </section>
  );
}

function EntityList({ entities }: { entities: Analysis["entities"] }) {
  const groups = Map.groupBy(entities, (e) => e.type);
  return (
    <dl className="space-y-2 text-sm">
      {[...groups].map(([type, list]) => (
        <div key={type} className="grid grid-cols-[7.5rem_1fr] gap-3">
          <dt className="text-muted">{ENTITY_LABEL[type]}</dt>
          <dd className="flex flex-wrap gap-1.5">
            {[...new Set(list.map((e) => e.value))].slice(0, 12).map((v) => (
              <code key={v} className="rounded bg-surface px-1.5 py-0.5 text-xs">{v}</code>
            ))}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line p-5">
      <h3 className="mb-4 font-semibold">{title}</h3>
      {children}
    </div>
  );
}
