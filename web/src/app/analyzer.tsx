"use client";

import { FileDown, Loader2, Upload, X } from "lucide-react";
import { useState } from "react";
import { analyze, loadClassifier, type Analysis } from "@/lib/analyze";
import type { Instance } from "@/lib/datajud";
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

function todayIso() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function Analyzer() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [selected, setSelected] = useState(0);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [dragging, setDragging] = useState(false);
  // nonce remonta a consulta mesmo quando o mesmo número é pedido de novo
  const [lookup, setLookup] = useState({ numero: "", nonce: 0 });
  // Termo inicial dos prazos (ficha e relatório). Vazio = hoje; calculado só no navegador, nunca na pré-renderização.
  const [intimationInput, setIntimation] = useState("");
  const intimation = () => intimationInput || todayIso();
  const [dockets, setDockets] = useState<Record<string, Instance[]>>({}); // andamentos consultados, entram no relatório
  const [reporting, setReporting] = useState(false);

  async function generateReport(onlyDocket?: string) {
    setReporting(true);
    try {
      const { downloadReport } = await import("@/lib/report"); // jsPDF só carrega quando pedido
      const ready = docs.filter((d): d is Required<Pick<Doc, "name" | "result">> & Doc => !!d.result);
      const date = new Date().toISOString().slice(0, 10);
      downloadReport(
        onlyDocket
          ? { docs: [], intimation: intimation(), dockets: { [onlyDocket]: dockets[onlyDocket] } }
          : { docs: ready.map((d) => ({ name: d.name, result: d.result })), intimation: intimation(), dockets },
        onlyDocket ? `andamento-${onlyDocket.replace(/\D/g, "")}.pdf` : `relatorio-processual-${date}.pdf`,
      );
    } catch {
      setNotice("Não foi possível gerar o relatório. Tente novamente.");
    } finally {
      setReporting(false);
    }
  }

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
          id="enviar"
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
        <div className="flex flex-wrap items-center gap-2 print:hidden">
          <button type="button" onClick={() => generateReport()} disabled={reporting || !docs.some((d) => d.result)}
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-on-accent disabled:opacity-40">
            {reporting ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <FileDown className="size-4" aria-hidden />}
            Gerar relatório em PDF
          </button>
          <span className="text-xs text-muted">
            {docs.length > 1 ? "Quadro-resumo e análise completa de cada documento" : "Análise completa do documento"}
            {Object.keys(dockets).length > 0 && ", com o andamento consultado no Datajud"}
          </span>
          <button type="button" onClick={() => setDocs([])}
            className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted hover:bg-surface">
            <X className="size-4" aria-hidden /> Limpar
          </button>
        </div>
      )}

      {docs.length > 1 && <BatchTable docs={docs} selected={selected} onSelect={setSelected} />}

      {current?.result && (
        <Result result={current.result} name={current.name} intimation={intimation()} onIntimation={setIntimation} onLookup={lookupProcess} />
      )}
      {current?.error && <p role="alert" className="rounded-lg border border-line bg-surface p-3 text-sm">{current.name}: {current.error}</p>}

      <section id="consulta" aria-labelledby="consulta-titulo" className="scroll-mt-6 rounded-xl border border-line bg-card p-5 print:hidden">
        <h2 id="consulta-titulo" className="font-display text-lg font-semibold">Consultar processo no Datajud (CNJ)</h2>
        <p className="mb-4 mt-1 text-sm text-muted">
          Metadados públicos: classe, assuntos, órgão julgador e todas as movimentações. Só o número do processo sai do seu
          navegador; os documentos analisados acima, não.
        </p>
        <ProcessLookup key={lookup.nonce} initial={lookup.numero}
          onResult={(numero, instances) => setDockets((d) => ({ ...d, [numero]: instances }))}
          onReport={(numero) => generateReport(numero)} />
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
            {["Documento", "Natureza", "Dispositivo", "Autos nº", "Prazos", "LGPD"].map((h) => (
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
