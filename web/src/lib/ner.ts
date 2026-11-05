// Extração de entidades jurídicas por regex, com validação de CPF/CNPJ (dígitos verificadores).
// Portado de src/infrastructure/nlp/ner_juridico.py (sem spaCy).

export type EntityType =
  | "CPF" | "CNPJ" | "RG" | "CNH" | "PIS" | "EMAIL" | "TELEFONE" | "ENDERECO" | "CEP" | "PLACA"
  | "PROCESSO_CNJ" | "OAB" | "DATA" | "VALOR" | "LEI" | "ARTIGO" | "TRIBUNAL" | "SUMULA" | "RECURSO";

export interface Entity {
  type: EntityType;
  value: string;
  start: number;
  end: number;
}

interface Pattern {
  type: EntityType;
  re: RegExp;
  personal: boolean; // dado pessoal (LGPD)
  priority: number; // vence em sobreposições
  validate?: (v: string) => boolean;
}

const digits = (v: string) => v.replace(/\D/g, "");

export function isValidCpf(v: string): boolean {
  const d = digits(v);
  if (d.length !== 11 || /^(\d)\1+$/.test(d)) return false;
  for (const len of [9, 10]) {
    let s = 0;
    for (let i = 0; i < len; i++) s += Number(d[i]) * (len + 1 - i);
    if (((s * 10) % 11) % 10 !== Number(d[len])) return false;
  }
  return true;
}

export function isValidCnpj(v: string): boolean {
  const d = digits(v);
  if (d.length !== 14 || /^(\d)\1+$/.test(d)) return false;
  const weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  for (const len of [12, 13]) {
    const w = weights.slice(13 - len);
    const r = w.reduce((s, wi, i) => s + Number(d[i]) * wi, 0) % 11;
    if ((r < 2 ? 0 : 11 - r) !== Number(d[len])) return false;
  }
  return true;
}

const MESES = "janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro";

const PATTERNS: Pattern[] = [
  { type: "PROCESSO_CNJ", re: /\b\d{7}[-.]?\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b/g, personal: false, priority: 15 },
  { type: "ENDERECO", re: /\b(?:Rua|Av\.?|Avenida|Travessa|Alameda|Rodovia|Praça)\s+[^\n,;]{3,80}?,?\s*(?:n[º°.]?\s*)?\d+/gi, personal: true, priority: 15 },
  { type: "CNH", re: /\bCNH\s*(?::|n[º°.]?)?\s*\d{11}\b/gi, personal: true, priority: 12 },
  { type: "PIS", re: /\b(?:PIS|NIS|PASEP)\s*(?::|n[º°.]?)?\s*\d{11}\b/gi, personal: true, priority: 12 },
  { type: "CEP", re: /\bCEP:?\s*\d{5}[-\s]?\d{3}\b/gi, personal: true, priority: 10 },
  { type: "CPF", re: /\b\d{3}[. ]?\d{3}[. ]?\d{3}[-. ]?\d{2}\b/g, personal: true, priority: 8, validate: isValidCpf },
  { type: "CNPJ", re: /\b\d{2}[. ]?\d{3}[. ]?\d{3}[/. ]?\d{4}[-. ]?\d{2}\b/g, personal: true, priority: 8, validate: isValidCnpj },
  { type: "RG", re: /\bRG\s*(?:n[º°.]?\s*)?[\d.-]{5,}\b/gi, personal: true, priority: 8 },
  { type: "EMAIL", re: /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, personal: true, priority: 8 },
  { type: "TELEFONE", re: /(?:\(\d{2}\)\s*|\+55\s*\d{2}\s*)(?:9\s*)?\d{4}[-\s]?\d{4}\b/g, personal: true, priority: 7 },
  { type: "LEI", re: /\b(?:Lei|LC|Decreto(?:-Lei)?)\s+(?:Complementar\s+)?(?:n[º°.]?\s*)?[\d.]+(?:\/\d{2,4})?/gi, personal: false, priority: 7 },
  { type: "DATA", re: new RegExp(`\\b(?:0?[1-9]|[12]\\d|3[01])\\/(?:0?[1-9]|1[0-2])\\/\\d{2,4}\\b|\\b\\d{1,2}\\s+de\\s+(?:${MESES})\\s+de\\s+\\d{4}\\b`, "gi"), personal: false, priority: 6 },
  { type: "PLACA", re: /\b[A-Z]{3}-?\d[A-Z0-9]\d{2}\b/g, personal: true, priority: 5 },
  { type: "OAB", re: /\bOAB[/\s-]?[A-Z]{2}\s*n?[º°.]?\s*[\d.]+/g, personal: false, priority: 4 },
  { type: "ARTIGO", re: /\bart(?:igo)?\.?\s*\d+(?:\.\d{3})*[º°]?/gi, personal: false, priority: 4 },
  { type: "RECURSO", re: /\b(?:REsp|AgRg|HC|RHC|MS|RMS|ADI|ADPF|ADC|RE|AI|ARE|Rcl)\s*n?[º°.]?\s*\d[\d.]*/g, personal: false, priority: 4 },
  { type: "VALOR", re: /R\$\s*[\d.]+(?:,\d{2})?/g, personal: false, priority: 2 },
  { type: "TRIBUNAL", re: /\b(?:STF|STJ|TST|TSE|STM|TRF\s?\d|TRT\s?\d+|TJ[A-Z]{2}|CNJ)\b/g, personal: false, priority: 1 },
  { type: "SUMULA", re: /\bS[úu]mula\s+(?:Vinculante\s+)?n?[º°.]?\s*\d+/gi, personal: false, priority: 1 },
];

const BY_TYPE = new Map(PATTERNS.map((p) => [p.type, p]));

export const isPersonal = (t: EntityType) => BY_TYPE.get(t)!.personal;

export function extractEntities(text: string): Entity[] {
  // Corrige confusões comuns de OCR em números; não muda o tamanho do texto, então as posições continuam válidas.
  const norm = text.replace(/(?<=\d)[Oo](?=\d)/g, "0").replace(/(?<=\d)l(?=\d)/g, "1");

  const found: Entity[] = [];
  for (const p of PATTERNS) {
    for (const m of norm.matchAll(p.re)) {
      const value = m[0].replace(/[\s,.;]+$/, "");
      if (p.validate && !p.validate(value)) continue;
      found.push({ type: p.type, value, start: m.index, end: m.index + value.length });
    }
  }

  // Em sobreposição, fica a entidade de maior prioridade
  found.sort((a, b) => a.start - b.start || BY_TYPE.get(b.type)!.priority - BY_TYPE.get(a.type)!.priority);
  const result: Entity[] = [];
  for (const e of found) {
    const last = result.at(-1);
    if (!last || e.start >= last.end) result.push(e);
    else if (BY_TYPE.get(e.type)!.priority > BY_TYPE.get(last.type)!.priority) result[result.length - 1] = e;
  }
  return result;
}

/** Substitui cada dado pessoal por [TIPO], para compartilhar o texto sem expor o titular. */
export function anonymize(text: string, entities: Entity[]): string {
  let out = "";
  let pos = 0;
  for (const e of entities) {
    if (!isPersonal(e.type)) continue;
    out += text.slice(pos, e.start) + `[${e.type}]`;
    pos = e.end;
  }
  return out + text.slice(pos);
}

const RISK_WEIGHTS: Partial<Record<EntityType, number>> = {
  CPF: 30, RG: 20, CNH: 20, EMAIL: 20, CNPJ: 15, PIS: 15, TELEFONE: 15, ENDERECO: 10, CEP: 5, PLACA: 5,
};

/** 0–100: soma dos pesos dos tipos de dado pessoal presentes (cada tipo conta uma vez). */
export function exposureScore(entities: Entity[]): { score: number; level: "Baixa" | "Média" | "Alta" } {
  const types = new Set(entities.map((e) => e.type));
  const score = Math.min(100, [...types].reduce((s, t) => s + (RISK_WEIGHTS[t] ?? 0), 0));
  return { score, level: score >= 50 ? "Alta" : score >= 20 ? "Média" : "Baixa" };
}
