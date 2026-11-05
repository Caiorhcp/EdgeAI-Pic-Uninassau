// Relatório de Análise Processual em PDF, gerado no navegador (jsPDF): nada sai do dispositivo.

import { jsPDF } from "jspdf";
import type { Analysis } from "./analyze";
import { courtOf } from "./cnj";
import type { Instance } from "./datajud";
import { dueDate, type Deadline } from "./deadlines";
import { daysBetween, describeMovement, humanDuration, milestoneOf, parseDatajudDate, redistributions } from "./movements";
import { isPersonal, type EntityType } from "./ner";

export interface ReportDoc {
  name: string;
  result: Analysis;
}

export interface ReportInput {
  docs: ReportDoc[];
  intimation: string; // AAAA-MM-DD informado pelo usuário, termo inicial dos prazos
  dockets: Record<string, Instance[]>; // andamentos consultados no Datajud, por número formatado
  now?: Date;
}

const PAGE = { w: 210, h: 297, margin: 20 };
const WIDTH = PAGE.w - 2 * PAGE.margin;
const INK = [23, 33, 31] as const; // cores do site (tinta, petróleo, ocre)
const BRAND = [31, 95, 99] as const;
const MUTED = [95, 105, 99] as const;
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"];

const PERSONAL_LABEL: Partial<Record<EntityType, string>> = {
  CPF: "CPF", CNPJ: "CNPJ", RG: "RG", CNH: "CNH", PIS: "PIS/NIS", EMAIL: "E-mail", TELEFONE: "Telefone",
  ENDERECO: "Endereço", CEP: "CEP", PLACA: "Placa de veículo",
};

const fmtIso = (iso: string) => new Date(`${iso}T00:00:00Z`).toLocaleDateString("pt-BR", { timeZone: "UTC" });
const fmtDj = (s: string | null) => parseDatajudDate(s)?.toLocaleDateString("pt-BR", { timeZone: "UTC" }) ?? "—";
/** No relatório o dado pessoal aparece mascarado: "529•••••••••" */
const mask = (v: string) => v.slice(0, 3) + v.slice(3).replace(/[\p{L}\d]/gu, "•");
const deadlineLabel = (d: Deadline) => `${d.amount} ${d.unit}${d.unit === "dias" ? (d.businessDays ? " úteis" : " corridos") : ""}`;

class Writer {
  readonly pdf = new jsPDF({ unit: "mm", format: "a4" });
  y = PAGE.margin + 8;

  private font(size: number, style: "normal" | "bold" | "italic" = "normal", color: readonly number[] = INK) {
    this.pdf.setFont("helvetica", style).setFontSize(size).setTextColor(color[0], color[1], color[2]);
  }

  newPage() {
    this.pdf.addPage();
    this.y = PAGE.margin + 8;
  }

  ensure(h: number) {
    if (this.y + h > PAGE.h - PAGE.margin - 8) this.newPage();
  }

  title(text: string, sub?: string) {
    this.font(18, "bold", BRAND);
    this.pdf.text(text, PAGE.margin, this.y);
    this.y += 8;
    if (sub) {
      this.font(10, "normal", MUTED);
      this.pdf.text(sub, PAGE.margin, this.y);
      this.y += 6;
    }
    this.rule();
  }

  rule() {
    this.pdf.setDrawColor(216, 207, 189).line(PAGE.margin, this.y, PAGE.w - PAGE.margin, this.y);
    this.y += 5;
  }

  h1(text: string) {
    this.ensure(18);
    this.y += 3;
    this.font(13, "bold", BRAND);
    this.pdf.text(text, PAGE.margin, this.y);
    this.y += 2;
    this.rule();
  }

  h2(text: string) {
    this.ensure(12);
    this.y += 1;
    this.font(10.5, "bold");
    this.pdf.text(text.toUpperCase(), PAGE.margin, this.y);
    this.y += 5.5;
  }

  para(text: string, opts: { indent?: number; style?: "normal" | "italic" | "bold"; color?: readonly number[]; size?: number } = {}) {
    const { indent = 0, style = "normal", color = INK, size = 10 } = opts;
    this.font(size, style, color);
    const lines: string[] = this.pdf.splitTextToSize(text, WIDTH - indent);
    for (const line of lines) {
      this.ensure(5);
      this.pdf.text(line, PAGE.margin + indent, this.y);
      this.y += size * 0.45;
    }
    this.y += 1.2;
  }

  kv(key: string, value: string) {
    this.font(10, "bold");
    const kw = this.pdf.getTextWidth(`${key}: `);
    this.font(10);
    const lines: string[] = this.pdf.splitTextToSize(value, WIDTH - kw);
    this.ensure(5 * Math.min(lines.length, 3));
    this.font(10, "bold");
    this.pdf.text(`${key}:`, PAGE.margin, this.y);
    this.font(10);
    lines.forEach((l, i) => {
      if (i > 0) this.ensure(5);
      this.pdf.text(l, PAGE.margin + kw, this.y);
      this.y += 4.5;
    });
    this.y += 0.8;
  }

  bullet(text: string, quote?: string) {
    this.para(`•  ${text}`, { indent: 2 });
    if (quote) this.para(`“${quote}”`, { indent: 7, style: "italic", color: MUTED, size: 9 });
  }

  table(cols: { title: string; width: number }[], rows: string[][]) {
    const pad = 1.5;
    const line = 3.9;
    const header = () => {
      this.ensure(9);
      this.pdf.setFillColor(239, 233, 220).rect(PAGE.margin, this.y - 4, WIDTH, 6.5, "F");
      this.font(8.5, "bold");
      let x = PAGE.margin;
      for (const c of cols) {
        this.pdf.text(c.title, x + pad, this.y);
        x += c.width;
      }
      this.y += 5;
    };
    header();
    this.font(8.5);
    for (const row of rows) {
      const cells = row.map((v, i) => this.pdf.splitTextToSize(v || "—", cols[i].width - 2 * pad) as string[]);
      const h = Math.max(...cells.map((c) => c.length)) * line + 1.5;
      if (this.y + h > PAGE.h - PAGE.margin - 8) {
        this.newPage();
        header();
        this.font(8.5);
      }
      let x = PAGE.margin;
      cells.forEach((c, i) => {
        c.forEach((l, k) => this.pdf.text(l, x + pad, this.y + k * line));
        x += cols[i].width;
      });
      this.y += h;
      this.pdf.setDrawColor(216, 207, 189).line(PAGE.margin, this.y - line + 0.5, PAGE.w - PAGE.margin, this.y - line + 0.5);
    }
    this.y += 3;
  }

  /** Cabeçalho e rodapé em todas as páginas, depois de tudo escrito (para saber o total). */
  finish(issued: string) {
    const total = this.pdf.getNumberOfPages();
    for (let p = 1; p <= total; p++) {
      this.pdf.setPage(p);
      this.font(8, "normal", MUTED);
      if (p > 1) this.pdf.text("S.A.P.O. · Relatório de Análise Processual", PAGE.margin, 12);
      this.pdf.text(
        `Gerado localmente em ${issued}. Relatório auxiliar elaborado por extração automática; não substitui a leitura dos autos.`,
        PAGE.margin, PAGE.h - 10, { maxWidth: WIDTH - 25 },
      );
      this.pdf.text(`Página ${p} de ${total}`, PAGE.w - PAGE.margin, PAGE.h - 10, { align: "right" });
    }
  }
}

function documentSections(w: Writer, { name, result: r }: ReportDoc, input: ReportInput) {
  let n = 0;
  const sec = (t: string) => w.h2(`${ROMAN[n++]}. ${t}`);
  const own = r.outcomes.filter((o) => o.own);
  const cited = r.outcomes.filter((o) => !o.own);

  sec("Identificação");
  w.kv("Arquivo", `${name} (${r.pages} ${r.pages === 1 ? "página" : "páginas"}${r.ocrPages ? `, ${r.ocrPages} digitalizada(s) com OCR` : ""})`);
  w.kv("Natureza da peça", `${r.ranking[0].label} (classificação automática, confiança de ${(r.ranking[0].probability * 100).toFixed(0)}%)`);
  w.kv("Autos nº", r.processNumbers.length ? r.processNumbers.map((p) => `${p} (${courtOf(p) ?? "DV inválido"})`).join("; ") : "não identificado");
  w.kv("Juízo / órgão julgador", r.header.body ?? "não identificado");
  if (r.header.district) w.kv("Comarca", r.header.district);
  if (r.header.judge) w.kv("Magistrado(a) / relator(a)", r.header.judge);
  if (r.header.action) w.kv("Natureza da ação", r.header.action);
  if (r.segments.length > 1) {
    w.kv("Peças por página", r.segments.map((s) => `${s.from === s.to ? `fl. ${s.from}` : `fls. ${s.from}–${s.to}`}: ${s.label}`).join("; "));
  }

  sec("Das partes e procuradores");
  const side = (s: "ativo" | "passivo") => r.parties.filter((p) => p.side === s).map((p) => `${p.name} (${p.role.toLowerCase()})`).join("; ") || "não identificado";
  w.kv("Polo ativo", side("ativo"));
  w.kv("Polo passivo", side("passivo"));
  w.kv("Procuradores", r.lawyers.length ? r.lawyers.map((l) => (l.name ? `${l.name}, ${l.oab}` : l.oab)).join("; ") : "não identificados");

  sec("Do dispositivo");
  if (own.length) own.forEach((o) => w.bullet(o.label, o.excerpt));
  else w.para("A peça não contém dispositivo decisório (trata-se de ato de parte ou de ato ordinatório).");
  if (cited.length) {
    w.para("Decisões anteriores mencionadas na peça:", { style: "bold" });
    cited.forEach((o) => w.bullet(o.label, o.excerpt));
  }

  if (r.requests.length) {
    sec("Dos pedidos");
    r.requests.forEach((q) => w.bullet(q));
  }

  sec("Dos prazos processuais");
  if (r.deadlines.length) {
    w.para(`Termo inicial considerado (intimação ou ciência): ${fmtIso(input.intimation)}.`);
    w.table(
      [{ title: "Prazo", width: 28 }, { title: "Termo final", width: 26 }, { title: "Ato / trecho", width: WIDTH - 54 }],
      r.deadlines.map((d) => {
        const due = dueDate(input.intimation, d);
        return [deadlineLabel(d), due ? fmtIso(due.toISOString().slice(0, 10)) : "contar da hora", d.excerpt];
      }),
    );
    w.para(
      "Contagem estimada nos termos dos arts. 219, 220 e 224 do CPC, considerados os feriados nacionais e o recesso forense " +
        "(20/12 a 20/1). Não abrange feriados estaduais ou municipais, suspensões determinadas pelo tribunal nem as regras de " +
        "termo inicial do art. 231 do CPC. Confira no sistema processual.",
      { size: 8.5, color: MUTED, style: "italic" },
    );
  } else w.para("Nenhum prazo assinalado no texto.");

  sec("Dos valores");
  if (r.values.length) r.values.forEach((v) => w.kv(v.label, v.value));
  else w.para("Nenhum valor mencionado.");

  sec("Da fundamentação normativa citada");
  const { laws, articles, precedents } = r.laws;
  if (laws.length + articles.length + precedents.length) {
    if (laws.length) w.kv("Diplomas legais", laws.join("; "));
    if (articles.length) w.kv("Dispositivos", articles.join("; "));
    if (precedents.length) w.kv("Súmulas e precedentes", precedents.join("; "));
    if (r.courts.length) w.kv("Tribunais mencionados", r.courts.join("; "));
  } else w.para("Nenhuma norma identificada.");

  sec("Da cronologia");
  if (r.events.length) {
    w.table([{ title: "Data", width: 22 }, { title: "Fato", width: WIDTH - 22 }], r.events.map((e) => [fmtIso(e.date), e.excerpt]));
  } else w.para("Nenhuma data identificada.");

  sec("Síntese do conteúdo");
  if (r.summary.length) r.summary.forEach((s, i) => w.para(`${i + 1}. ${s}`, { indent: 2 }));
  else w.para("Texto insuficiente para síntese.");

  sec("Do tratamento de dados pessoais (Lei 13.709/2018)");
  const personal = r.entities.filter((e) => isPersonal(e.type));
  w.kv("Índice de exposição", `${r.exposure.score}/100 (${r.exposure.level.toLowerCase()})`);
  if (personal.length) {
    const byType = Map.groupBy(personal, (e) => e.type);
    for (const [type, list] of byType) {
      w.kv(PERSONAL_LABEL[type] ?? type, [...new Set(list.map((e) => mask(e.value)))].join("; "));
    }
    w.para("Valores mascarados neste relatório. A versão anonimizada do texto pode ser baixada no S.A.P.O.", { size: 8.5, color: MUTED, style: "italic" });
  } else w.para("Nenhum dado pessoal identificado.");

  const dockets = r.processNumbers.filter((p) => input.dockets[p]);
  if (dockets.length) {
    sec("Do andamento processual (Datajud/CNJ)");
    dockets.forEach((p) => docketSection(w, p, input.dockets[p], input.now ?? new Date()));
  }
}

function docketSection(w: Writer, numero: string, instances: Instance[], now: Date) {
  for (const inst of instances) {
    w.para(`${numero} · ${inst.court} · ${inst.degree}`, { style: "bold" });
    const moves = inst.movements.map((m) => ({ ...m, milestone: milestoneOf(m.name, m.code) }));
    const closing = moves.find((m) => m.milestone === "Baixa / arquivamento" || m.milestone === "Trânsito em julgado");
    const currentBody = moves.find((m) => m.body)?.body ?? inst.body;
    w.kv("Classe", inst.className || "—");
    w.kv("Órgão julgador atual", currentBody || "—");
    const redists = redistributions(moves);
    if (redists.length) w.kv("Redistribuições", redists.map((r) => `${fmtDj(r.date)}: de ${r.from} para ${r.to}`).join("; "));
    w.kv("Assuntos", inst.subjects.join("; ") || "—");
    const filed = parseDatajudDate(inst.filedAt);
    const last = parseDatajudDate(moves[0]?.date ?? null);
    w.kv("Ajuizamento", `${fmtDj(inst.filedAt)}${filed ? ` (tramitação há ${humanDuration(daysBetween(filed, now))})` : ""}`);
    w.kv("Última movimentação", last ? `${fmtDj(moves[0].date)} (há ${humanDuration(daysBetween(last, now))})` : "—");
    w.kv("Situação", closing
      ? `${closing.milestone === "Trânsito em julgado" ? "trânsito em julgado" : "arquivado / baixado"} em ${fmtDj(closing.date)}`
      : "em andamento");
    if (moves.length) {
      w.table(
        [{ title: "Data", width: 22 }, { title: "Movimentação", width: WIDTH - 62 }, { title: "Marco", width: 40 }],
        moves.map((m) => [
          fmtDj(m.date),
          describeMovement(m) + (m.body && m.body !== currentBody ? ` · ${m.body}` : ""),
          m.milestone ?? "",
        ]),
      );
    }
  }
}

export function buildReport(input: ReportInput): jsPDF {
  const now = input.now ?? new Date();
  const issued = `${now.toLocaleDateString("pt-BR")} às ${now.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`;
  const w = new Writer();
  w.title("Relatório de Análise Processual", `S.A.P.O. – Sistema de Análise de Peças Offline · emitido em ${issued}`);

  if (input.docs.length > 1) {
    w.h1("Quadro-resumo");
    w.table(
      [{ title: "Documento", width: 42 }, { title: "Natureza", width: 26 }, { title: "Dispositivo", width: 34 }, { title: "Autos nº", width: 44 }, { title: "Prazos", width: WIDTH - 146 }],
      input.docs.map(({ name, result: r }) => [
        name, r.ranking[0].label, r.outcomes.find((o) => o.own)?.label ?? "—", r.processNumbers[0] ?? "—",
        r.deadlines.map(deadlineLabel).join("; "),
      ]),
    );
  }

  input.docs.forEach((d, i) => {
    if (i > 0 || input.docs.length > 1) w.newPage();
    w.h1(input.docs.length > 1 ? `Documento ${i + 1} de ${input.docs.length}: ${d.name}` : `Documento: ${d.name}`);
    documentSections(w, d, input);
  });

  // Andamentos consultados que não pertencem a nenhum documento analisado
  const loose = Object.keys(input.dockets).filter((p) => !input.docs.some((d) => d.result.processNumbers.includes(p)));
  if (loose.length) {
    if (input.docs.length) w.newPage();
    w.h1("Andamento processual (Datajud/CNJ)");
    loose.forEach((p) => docketSection(w, p, input.dockets[p], now));
  }

  w.h2("Nota metodológica");
  w.para(
    "A natureza da peça é estimada por modelo de aprendizado de máquina treinado no conjunto VICTOR (peças de recursos " +
      "extraordinários do STF). Partes, dispositivo, prazos, valores e datas são extraídos por regras sobre o texto. " +
      "O processamento ocorreu integralmente no dispositivo do usuário; apenas eventuais consultas ao Datajud foram " +
      "enviadas à API pública do CNJ. As informações devem ser conferidas com os autos.",
    { size: 8.5, color: MUTED },
  );

  w.finish(issued);
  return w.pdf;
}

export function downloadReport(input: ReportInput, filename: string) {
  buildReport(input).save(filename);
}
