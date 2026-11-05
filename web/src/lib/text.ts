/**
 * A frase que contém o trecho [start, end), com espaços normalizados.
 * Só termina em . ! ? ; seguidos de espaço: "R$ 8.000,00" e quebras de linha do PDF não cortam a frase.
 */
// Abreviações cujo ponto não encerra a frase ("art. 5º", "fls. 10", "Dr. Fulano")
const ABBREV = /\b(?:art|arts|inc|incs|al|fl|fls|n|nº|p|pp|ex|exmo|exma|sr|sra|dr|dra|min|des|rel|proc|cf)$/i;
const isBoundary = (text: string, dot: number) => text[dot] !== "." || !ABBREV.test(text.slice(Math.max(0, dot - 6), dot));

export function sentenceAt(text: string, start: number, end = start, max = 260): string {
  let from = 0;
  for (const m of text.slice(0, start).matchAll(/[.!?;]\s/g)) if (isBoundary(text, m.index)) from = m.index + 1;
  let to = text.length;
  for (const m of text.slice(end).matchAll(/[.!?;](?=\s|$)/g)) {
    if (isBoundary(text, end + m.index)) { to = end + m.index + 1; break; }
  }
  const s = text.slice(from, to).replace(/\s+/g, " ").trim();
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}
