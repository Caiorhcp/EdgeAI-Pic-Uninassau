"use client";

import { FileSpreadsheet, Loader2, Printer, Upload, X } from "lucide-react";
import { useState } from "react";
import { analyze, loadClassifier, type Analysis } from "@/lib/analyze";
import { courtOf } from "@/lib/cnj";
import { downloadFile, toCsv } from "@/lib/csv";
import type { Page } from "@/lib/pdf";
import { EXAMPLE_PAGES } from "./example";
import { ProcessLookup } from "./process-lookup";
import { Result } from "./result";

interface Doc {
  name: string;
  result?: Analysis;
  error?: string;
}

interface Job {
  name: string;
  getPages: (progress: (m: string) => void) => Promise<Page[]>;
}

const MAX_FILES = 30;

export function Analyzer() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [selected, setSelected] = useState(0);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [dragging, setDragging] = useState(false);
  // nonce remonta a consulta mesmo quando o mesmo número é pedido de novo
  const [lookup, setLookup] = useState({ numero: "", nonce: 0 });

  function lookupProcess(numero: string) {
    setLookup((l) => ({ numero, nonce: l.nonce + 1 }));
    document.getElementById("consulta")?.scrollIntoView({ behavior: "smooth" });
  }

  async function run(jobs: Job[]) {
    setNotice(null);
    const done: Doc[] = [];
    try {
      setBusy("Carregando modelo");
      const clf = await loadClassifier();
      for (const [i, job] of jobs.entries()) {
        const prefix = jobs.length > 1 ? `${job.name} (${i + 1} de ${jobs.length}): ` : "";
        try {
          const pages = await job.getPages((msg) => setBusy(prefix + msg));
          if (!pages.some((p) => p.text.trim())) throw new Error("Não foi possível extrair texto deste documento.");
          done.push({ name: job.name, result: analyze(clf, pages) });
        } catch (e) {
          done.push({ name: job.name, error: e instanceof Error ? e.message : "Erro inesperado." });
        }
      }
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Erro inesperado.");
    } finally {
      setBusy(null);
    }
    setDocs(done);
    setSelected(Math.max(0, done.findIndex((d) => d.result)));
  }

  function onFiles(list: FileList | null | undefined) {
    const files = [...(list ?? [])];
    const pdfs = files.filter((f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
    if (!pdfs.length) return files.length && setNotice("Envie arquivos PDF.");
    if (pdfs.length > MAX_FILES) setNotice(`Analisando os primeiros ${MAX_FILES} de ${pdfs.length} arquivos.`);
    run(pdfs.slice(0, MAX_FILES).map((file) => ({
      name: file.name,
      getPages: async (progress) => (await import("@/lib/pdf")).readPdf(file, progress),
    })));
  }

  const current = docs[selected];

  return (
    <div className="space-y-8">
      <section className="grid gap-4 md:grid-cols-2 print:hidden">
        <label
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); onFiles(e.dataTransfer.files); }}
          className={`flex min-h-48 cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-6 text-center transition ${dragging ? "border-accent bg-accent/5" : "border-line hover:border-accent/60"}`}
        >
          <Upload className="size-8 text-muted" aria-hidden />
          <span className="font-medium">Arraste PDFs ou clique para escolher</span>
          <span className="text-sm text-muted">Um ou vários de uma vez (até {MAX_FILES}), digitais ou escaneados</span>
          <input type="file" accept="application/pdf" multiple className="sr-only" disabled={!!busy}
            onChange={(e) => { onFiles(e.target.files); e.target.value = ""; }} />
        </label>

        <div className="flex flex-col gap-3">
          <label htmlFor="texto" className="sr-only">Texto do documento</label>
          <textarea id="texto" value={text} onChange={(e) => setText(e.target.value)} disabled={!!busy}
            placeholder="…ou cole o texto de uma peça processual aqui"
            className="min-h-36 flex-1 resize-y rounded-xl border border-line bg-card p-4 text-sm outline-none focus:border-accent" />
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={!!busy || !text.trim()}
              onClick={() => run([{ name: "Texto colado", getPages: async () => [{ number: 1, text, ocr: false }] }])}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-on-accent disabled:opacity-40">
              Analisar texto
            </button>
            <button type="button" disabled={!!busy} onClick={() => run([{ name: "Exemplo", getPages: async () => EXAMPLE_PAGES }])}
              className="rounded-lg border border-line px-4 py-2 text-sm font-medium hover:bg-surface disabled:opacity-40">
              Usar documento de exemplo
            </button>
          </div>
        </div>
      </section>

      <div aria-live="polite" className="print:hidden">
        {busy && (
          <p className="flex items-center gap-2 text-sm text-muted">
            <Loader2 className="size-4 animate-spin" aria-hidden /> {busy}…
          </p>
        )}
        {notice && (
          <p role="alert" className="rounded-lg border border-line bg-surface p-3 text-sm">{notice}</p>
        )}
      </div>

      {docs.length > 0 && (
        <div className="flex flex-wrap gap-2 print:hidden">
          <button type="button" onClick={() => exportCsv(docs)}
            className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium hover:bg-surface">
            <FileSpreadsheet className="size-4" aria-hidden /> Exportar planilha (CSV)
          </button>
          <button type="button" onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium hover:bg-surface">
            <Printer className="size-4" aria-hidden /> Imprimir ou salvar PDF
          </button>
          <button type="button" onClick={() => setDocs([])}
            className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted hover:bg-surface">
            <X className="size-4" aria-hidden /> Limpar
          </button>
        </div>
      )}

      {docs.length > 1 && <BatchTable docs={docs} selected={selected} onSelect={setSelected} />}

      {current?.result && <Result result={current.result} name={current.name} onLookup={lookupProcess} />}
      {current?.error && <p role="alert" className="rounded-lg border border-line bg-surface p-3 text-sm">{current.name}: {current.error}</p>}

      <section id="consulta" aria-labelledby="consulta-titulo" className="scroll-mt-6 rounded-xl border border-line bg-card p-5 print:hidden">
        <h2 id="consulta-titulo" className="font-display text-lg font-semibold">Consultar processo no Datajud (CNJ)</h2>
        <p className="mb-4 mt-1 text-sm text-muted">
          Metadados públicos: classe, assuntos, órgão julgador e todas as movimentações. Só o número do processo sai do seu
          navegador; os documentos analisados acima, não.
        </p>
        <ProcessLookup key={lookup.nonce} initial={lookup.numero} />
      </section>
    </div>
  );
}

const mainOutcome = (r: Analysis) => r.outcomes.find((o) => o.own)?.label ?? "—";
const deadlinesText = (r: Analysis) =>
  r.deadlines.map((d) => `${d.amount} ${d.unit}${d.unit === "dias" ? (d.businessDays ? " úteis" : " corridos") : ""}`).join(", ") || "—";

function BatchTable({ docs, selected, onSelect }: { docs: Doc[]; selected: number; onSelect: (i: number) => void }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-card">
      <table className="w-full text-left text-sm">
        <caption className="px-4 pt-4 text-left font-display text-lg font-semibold">Triagem de {docs.length} documentos</caption>
        <thead>
          <tr className="border-b border-line text-muted">
            {["Arquivo", "Tipo", "Resultado", "Processo", "Prazos", "LGPD"].map((h) => (
              <th key={h} className="px-4 py-2 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {docs.map((d, i) => (
            <tr key={i} onClick={() => d.result && onSelect(i)} aria-selected={i === selected}
              className={`border-b border-line last:border-0 ${d.result ? "cursor-pointer hover:bg-surface" : ""} ${i === selected ? "bg-accent/10" : ""}`}>
              <td className="px-4 py-2">
                {d.result ? (
                  <button type="button" onClick={() => onSelect(i)} className="text-left font-medium underline-offset-2 hover:underline">{d.name}</button>
                ) : d.name}
              </td>
              {d.result ? (
                <>
                  <td className="px-4 py-2">{d.result.ranking[0].label}</td>
                  <td className="px-4 py-2">{mainOutcome(d.result)}</td>
                  <td className="whitespace-nowrap px-4 py-2 font-mono text-xs">{d.result.processNumbers[0] ?? "—"}</td>
                  <td className="px-4 py-2">{deadlinesText(d.result)}</td>
                  <td className="px-4 py-2 tabular-nums">{d.result.exposure.score}</td>
                </>
              ) : (
                <td colSpan={5} className="px-4 py-2 text-muted">{d.error}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function exportCsv(docs: Doc[]) {
  const header = ["Arquivo", "Páginas", "Tipo provável", "Confiança", "Resultado", "Decisões citadas", "Processos", "Tribunal do processo", "Tribunais citados",
    "Polo ativo", "Polo passivo", "Advogados", "Prazos", "Valores", "Exposição LGPD", "Erro"];
  const rows = docs.map(({ name, result: r, error }) => r ? [
    name, r.pages, r.ranking[0].label, `${(r.ranking[0].probability * 100).toFixed(0)}%`, mainOutcome(r),
    [...new Set(r.outcomes.filter((o) => !o.own).map((o) => o.label))].join(", "),
    r.processNumbers.join(", "), r.processNumbers.map((n) => courtOf(n) ?? "?").join(", "), r.courts.join(", "),
    r.parties.filter((p) => p.side === "ativo").map((p) => p.name).join("; "),
    r.parties.filter((p) => p.side === "passivo").map((p) => p.name).join("; "),
    r.lawyers.map((l) => (l.name ? `${l.name} (${l.oab})` : l.oab)).join("; "),
    deadlinesText(r), r.values.map((v) => `${v.label}: ${v.value}`).join("; "), r.exposure.score, "",
  ] : [name, ...Array<string>(header.length - 2).fill(""), error ?? ""]);
  downloadFile(`sapo-triagem-${new Date().toISOString().slice(0, 10)}.csv`, toCsv(header, rows));
}
