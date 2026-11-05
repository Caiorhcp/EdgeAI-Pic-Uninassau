// Prazos encontrados no texto e cálculo do vencimento.
// Regras: CPC art. 219 (dias úteis), art. 220 (suspensão de 20/12 a 20/1) e art. 224 (exclui o dia do começo).
// Só feriados nacionais e dias sem expediente forense comuns; feriados locais não entram.

import { sentenceAt } from "./text";

export type Unit = "dias" | "horas" | "meses" | "anos";

export interface Deadline {
  amount: number;
  unit: Unit;
  businessDays: boolean; // dias úteis (padrão do CPC) ou corridos
  excerpt: string; // trecho onde o prazo aparece
}

const WORDS: Record<string, number> = {
  um: 1, uma: 1, dois: 2, duas: 2, "três": 3, tres: 3, quatro: 4, cinco: 5, seis: 6, sete: 7, oito: 8, nove: 9,
  dez: 10, onze: 11, doze: 12, treze: 13, quatorze: 14, catorze: 14, quinze: 15, dezesseis: 16, dezessete: 17,
  dezoito: 18, dezenove: 19, vinte: 20, trinta: 30, quarenta: 40, cinquenta: 50, sessenta: 60, noventa: 90,
  "vinte e quatro": 24, "quarenta e oito": 48, "setenta e duas": 72, "quarenta e cinco": 45, "cento e vinte": 120,
};
const WORD_RE = Object.keys(WORDS).sort((a, b) => b.length - a.length).join("|");

const DEADLINE_RE = new RegExp(
  String.raw`\b(?:prazo(?:\s+(?:legal|comum|sucessivo|improrrogável|de\s+lei))?\s+de|em\s+até|dentro\s+de|em)\s+` +
    String.raw`(\d{1,3}|${WORD_RE})\s*(?:\(\s*[a-zà-ú\s]+\)\s*)?(dias?|horas?|m[eê]s(?:es)?|anos?)(\s+(?:úteis|corridos))?`,
  "gi",
);

export function findDeadlines(text: string): Deadline[] {
  const seen = new Set<string>();
  const out: Deadline[] = [];
  for (const m of text.matchAll(DEADLINE_RE)) {
    const amount = /^\d+$/.test(m[1]) ? Number(m[1]) : WORDS[m[1].toLowerCase()];
    const u = m[2].toLowerCase();
    const unit: Unit = u.startsWith("dia") ? "dias" : u.startsWith("hora") ? "horas" : u.startsWith("ano") ? "anos" : "meses";
    const excerpt = sentenceAt(text, m.index, m.index + m[0].length);
    const key = `${amount}-${unit}-${excerpt}`;
    if (!amount || seen.has(key)) continue;
    seen.add(key);
    out.push({ amount, unit, businessDays: unit === "dias" && !/corridos/i.test(m[3] ?? ""), excerpt });
  }
  return out;
}

// ---- calendário (datas em UTC para não depender do fuso do navegador) ----

const day = (y: number, m: number, d: number) => new Date(Date.UTC(y, m - 1, d));
const addDays = (date: Date, n: number) => new Date(date.getTime() + n * 86_400_000);
const key = (d: Date) => d.toISOString().slice(0, 10);

/** Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher). */
export function easter(y: number): Date {
  const a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4;
  const f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31), dayOfMonth = ((h + l - 7 * m + 114) % 31) + 1;
  return day(y, month, dayOfMonth);
}

const holidayCache = new Map<number, Set<string>>();
function holidays(y: number): Set<string> {
  let set = holidayCache.get(y);
  if (!set) {
    const e = easter(y);
    set = new Set([
      // Feriados nacionais (Lei 662/1949; 20/11 pela Lei 14.759/2023)
      ...[[1, 1], [4, 21], [5, 1], [9, 7], [10, 12], [11, 2], [11, 15], [11, 20], [12, 25]].map(([m, d]) => key(day(y, m, d))),
      // Sem expediente forense na maior parte dos tribunais
      key(addDays(e, -48)), key(addDays(e, -47)), // Carnaval
      key(addDays(e, -2)), // Sexta-feira Santa
      key(addDays(e, 60)), // Corpus Christi
    ]);
    holidayCache.set(y, set);
  }
  return set;
}

const inRecess = (d: Date) => {
  const m = d.getUTCMonth() + 1, dd = d.getUTCDate();
  return (m === 12 && dd >= 20) || (m === 1 && dd <= 20); // CPC art. 220
};

export function isBusinessDay(d: Date): boolean {
  const w = d.getUTCDay();
  return w !== 0 && w !== 6 && !holidays(d.getUTCFullYear()).has(key(d)) && !inRecess(d);
}

/** Vencimento contando a partir do dia seguinte à intimação (`start`, em "AAAA-MM-DD"). */
export function dueDate(start: string, dl: Deadline): Date | null {
  const [y, m, d] = start.split("-").map(Number);
  let date = day(y, m, d);
  if (dl.unit === "horas") return null; // depende da hora exata da intimação
  if (dl.unit === "meses" || dl.unit === "anos") {
    const months = dl.unit === "anos" ? dl.amount * 12 : dl.amount;
    date = day(y, m + months, d);
  } else if (dl.businessDays) {
    for (let left = dl.amount; left > 0; ) {
      date = addDays(date, 1);
      if (isBusinessDay(date)) left--;
    }
    return date;
  } else {
    date = addDays(date, dl.amount);
  }
  while (!isBusinessDay(date)) date = addDays(date, 1); // art. 224, §1º: vencimento em dia sem expediente é prorrogado
  return date;
}
