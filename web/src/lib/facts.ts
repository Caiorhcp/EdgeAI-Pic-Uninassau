// Fatos principais de uma peça: partes, advogados, resultado da decisão, valores e datas.
// Regras sobre o texto; servem para triagem e precisam de conferência humana.

import type { Entity } from "./ner";
import { sentenceAt } from "./text";

export type Side = "ativo" | "passivo";

export interface Party {
  role: string; // "Recorrente", "Réu"...
  name: string;
  side: Side;
}

export interface Lawyer {
  name: string | null;
  oab: string; // "OAB/RS 12.345"
}

export interface Outcome {
  label: string; // "Não provido", "Procedente"...
  own: boolean; // true: dispositivo desta peça ("nego provimento"); false: decisão citada ("a sentença julgou...")
  excerpt: string;
}

export interface LabeledValue {
  label: string;
  value: string;
}

export interface DatedEvent {
  date: string; // AAAA-MM-DD
  excerpt: string;
}

const ROLES: [RegExp, string, Side][] = [
  [/autora?e?s?/, "Autor", "ativo"], [/r[ée]us?|ré/, "Réu", "passivo"],
  [/requerente/, "Requerente", "ativo"], [/requerid[oa]/, "Requerido", "passivo"],
  [/recorrente/, "Recorrente", "ativo"], [/recorrid[oa]/, "Recorrido", "passivo"],
  [/agravante/, "Agravante", "ativo"], [/agravad[oa]/, "Agravado", "passivo"],
  [/apelante/, "Apelante", "ativo"], [/apelad[oa]/, "Apelado", "passivo"],
  [/impetrante/, "Impetrante", "ativo"], [/impetrad[oa]/, "Impetrado", "passivo"],
  [/exequente/, "Exequente", "ativo"], [/executad[oa]/, "Executado", "passivo"],
  [/reclamante/, "Reclamante", "ativo"], [/reclamad[oa]/, "Reclamado", "passivo"],
  [/embargante/, "Embargante", "ativo"], [/embargad[oa]/, "Embargado", "passivo"],
];
const ROLE_WORDS =
  "autora?|autores|r[ée]us?|ré|requerentes?|requerid[oa]s?|recorrentes?|recorrid[oa]s?|agravantes?|agravad[oa]s?|" +
  "apelantes?|apelad[oa]s?|impetrantes?|impetrad[oa]s?|exequentes?|executad[oa]s?|reclamantes?|reclamad[oa]s?|embargantes?|embargad[oa]s?";
const LABELED_PARTY = new RegExp(`\\b(${ROLE_WORDS})\\s*:\\s*([^\\n;:]{2,120}?)(?=\\s*(?:\\.(?=\\s|$)|;|\\n|$|\\b(?:${ROLE_WORDS}|advogad[oa]s?|relator)\\s*:))`, "gi"); // ponto só encerra se seguido de espaço ("S.A." continua)

const clean = (s: string) => s.replace(/\s+/g, " ").replace(/[\s,.;–-]+$/, "").trim();
const title = (s: string) => (s === s.toUpperCase() ? s.toLowerCase().replace(/(^|\s)(\p{L})/gu, (_, a, b) => a + b.toUpperCase()) : s);

export function findParties(text: string): Party[] {
  const out: Party[] = [];
  const add = (role: string, name: string, side: Side) => {
    name = title(clean(name));
    if (name.length >= 3 && !out.some((p) => p.name.toLowerCase() === name.toLowerCase())) out.push({ role, name, side });
  };
  for (const m of text.matchAll(LABELED_PARTY)) {
    const found = ROLES.find(([re]) => new RegExp(`^(?:${re.source})$`, "i").test(m[1]));
    if (found) add(found[1], m[2], found[2]);
  }
  // Qualificação: "FULANO DE TAL, brasileiro, ... vem ... em face de BELTRANO"
  for (const m of text.matchAll(/(?:^|\n|\.\s)([A-ZÀ-Ú][A-ZÀ-Ú\s.]{4,80}?),\s*(?:brasileir|pessoa jurídica|inscrit|portador|nacionalidade|estrangeir)/g)) {
    add("Parte (qualificação)", m[1], "ativo");
  }
  for (const m of text.matchAll(/\bem face d[aoe]s?\s+([A-ZÀ-Ú][\wÀ-ú.\s]{2,80}?)(?=[,.;\n]|\s+(?:pelas|pelos|com|por)\b)/g)) {
    add("Parte contrária", m[1], "passivo");
  }
  return out;
}

export function findLawyers(text: string): Lawyer[] {
  const out: Lawyer[] = [];
  const re = /(?:([A-ZÀ-Ú][a-zà-ú]+(?:\s+(?:d[aeo]s?\s+)?[A-ZÀ-Ú][a-zà-ú]+){1,5})\s*[,(–-]?\s*)?OAB\s*[/-]?\s*([A-Z]{2})\s*(?:n[º°.]?\s*)?(\d[\d.]*\d)/g;
  for (const m of text.matchAll(re)) {
    const oab = `OAB/${m[2]} ${m[3]}`;
    if (!out.some((l) => l.oab === oab)) out.push({ name: m[1] ?? null, oab });
  }
  return out;
}

// Verbos em 1ª pessoa no presente = dispositivo da própria peça; no passado = decisão citada
const OUTCOMES: [RegExp, string, boolean][] = [
  [/julgo\s+parcialmente\s+procedentes?/i, "Parcialmente procedente", true],
  [/julgo\s+improcedentes?/i, "Improcedente", true],
  [/julgo\s+procedentes?/i, "Procedente", true],
  [/(?:dou|dá-se)\s+parcial\s+provimento/i, "Parcialmente provido", true],
  [/(?:dou|dá-se)\s+provimento/i, "Provido", true],
  [/(?:nego|nega-se)\s+provimento/i, "Não provido", true],
  [/nego\s+seguimento/i, "Seguimento negado", true],
  [/não\s+(?:admito|conheço)/i, "Não admitido", true],
  [/\badmito\s+o\s+recurso/i, "Recurso admitido", true],
  [/extingo\s+o\s+(?:processo|feito)[^.]{0,40}sem\s+resolução/i, "Extinto sem resolução do mérito", true],
  [/extingo\s+o\s+(?:processo|feito)[^.]{0,40}com\s+resolução/i, "Extinto com resolução do mérito", true],
  [/\bhomologo\b/i, "Homologado", true],
  [/\bdefiro\s+(?:a\s+|o\s+)?(?:tutela|liminar|pedido)/i, "Deferido", true],
  [/\bindefiro\s+(?:a\s+|o\s+)?(?:tutela|liminar|pedido)/i, "Indeferido", true],
  [/julgou\s+parcialmente\s+procedentes?/i, "Parcialmente procedente", false],
  [/julgou\s+improcedentes?/i, "Improcedente", false],
  [/julgou\s+procedentes?/i, "Procedente", false],
  [/negou\s+provimento/i, "Não provido", false],
  [/deu\s+(?:parcial\s+)?provimento/i, "Provido", false],
];

export function findOutcomes(text: string): Outcome[] {
  const flat = text.replace(/\s+/g, " ");
  const out: Outcome[] = [];
  const taken: [number, number][] = [];
  for (const [re, label, own] of OUTCOMES) {
    for (const m of flat.matchAll(new RegExp(re.source, "gi"))) {
      const [s, e] = [m.index, m.index + m[0].length];
      if (taken.some(([a, b]) => s < b && e > a)) continue; // "parcialmente procedente" não vira também "procedente"
      taken.push([s, e]);
      out.push({ label, own, excerpt: sentenceAt(flat, s, e) });
    }
  }
  return out.sort((a, b) => Number(b.own) - Number(a.own));
}

const VALUE_LABELS: [RegExp, string][] = [
  [/valor\s+da\s+causa/i, "Valor da causa"], [/danos?\s+morais/i, "Danos morais"], [/danos?\s+materiais/i, "Danos materiais"],
  [/honorários/i, "Honorários"], [/multa|astreintes/i, "Multa"], [/custas/i, "Custas"],
  [/condena|diferenças|atrasados|pagamento/i, "Condenação / pagamento"],
];

export function labelValues(text: string, entities: Entity[]): LabeledValue[] {
  return entities
    .filter((e) => e.type === "VALOR")
    .map((e) => {
      const before = text.slice(Math.max(0, e.start - 90), e.start);
      // O rótulo mais próximo do valor vence ("valor da causa de R$ X e danos morais de R$ Y")
      let best = { label: "Valor citado", at: -1 };
      for (const [re, label] of VALUE_LABELS) {
        for (const m of before.matchAll(new RegExp(re.source, "gi"))) if (m.index > best.at) best = { label, at: m.index };
      }
      return { label: best.label, value: e.value };
    })
    .filter((v, i, all) => all.findIndex((w) => w.value === v.value && w.label === v.label) === i);
}

const MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];

export function parseDate(s: string): string | null {
  let m = s.match(/(\d{1,2})\/(\d{1,2})\/(\d{2,4})/);
  if (m) {
    const y = m[3].length === 2 ? 2000 + Number(m[3]) : Number(m[3]);
    return `${y}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}`;
  }
  m = s.toLowerCase().match(/(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})/);
  const month = m ? MONTHS.indexOf(m[2]) + 1 : 0;
  return m && month ? `${m[3]}-${String(month).padStart(2, "0")}-${m[1].padStart(2, "0")}` : null;
}

export function timeline(text: string, entities: Entity[]): DatedEvent[] {
  const events = entities
    .filter((e) => e.type === "DATA")
    .map((e) => ({ date: parseDate(e.value), excerpt: sentenceAt(text, e.start, e.end, 200) }))
    .filter((e): e is DatedEvent => e.date !== null);
  return events
    .filter((e, i) => events.findIndex((f) => f.date === e.date && f.excerpt === e.excerpt) === i)
    .sort((a, b) => a.date.localeCompare(b.date));
}
