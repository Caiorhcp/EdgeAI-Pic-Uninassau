// Número único de processo (Resolução CNJ 65/2008): NNNNNNN-DD.AAAA.J.TR.OOOO

const UFS = ["ac", "al", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms", "mg", "pa", "pb", "pr", "pe", "pi",
  "rj", "rn", "rs", "ro", "rr", "sc", "se", "sp", "to"]; // ordem do código TR da Justiça Estadual (01 = AC ... 27 = TO)

export interface Cnj {
  formatted: string;
  digits: string;
  segment: string; // J
  court: string; // TR
}

/** Aceita com ou sem pontuação; null se não tiver 20 dígitos ou o dígito verificador não bater. */
export function parseCnj(input: string): Cnj | null {
  const d = input.replace(/\D/g, "");
  if (d.length !== 20) return null;
  const [n, dv, year, j, tr, origin] = [d.slice(0, 7), d.slice(7, 9), d.slice(9, 13), d[13], d.slice(14, 16), d.slice(16)];
  // ISO 7064 MOD 97-10: DD = 98 - (N AAAA J TR OOOO 00 mod 97)
  const expected = 98 - Number(BigInt(n + year + j + tr + origin + "00") % 97n);
  if (expected !== Number(dv)) return null;
  return { formatted: `${n}-${dv}.${year}.${j}.${tr}.${origin}`, digits: d, segment: j, court: tr };
}

/** Sigla do tribunal pelo número ("TRF4", "TJSP", "STF"), ou null se o número for inválido. */
export function courtOf(numero: string): string | null {
  const cnj = parseCnj(numero);
  if (!cnj) return null;
  if (cnj.segment === "1") return "STF";
  if (cnj.segment === "2") return "CNJ";
  return datajudAlias(cnj)?.toUpperCase().replace("TRE-DFT", "TRE-DF") ?? null;
}

/** Alias do índice no Datajud, ou null quando o tribunal não está na API pública (ex.: STF). */
export function datajudAlias({ segment, court }: Cnj): string | null {
  const tr = Number(court);
  const uf = UFS[tr - 1];
  switch (segment) {
    case "3": return "stj";
    case "4": return tr >= 1 && tr <= 6 ? `trf${tr}` : null;
    case "5": return tr === 0 ? "tst" : tr <= 24 ? `trt${tr}` : null;
    case "6": return tr === 0 ? "tse" : uf ? `tre-${uf === "df" ? "dft" : uf}` : null;
    case "7": return tr === 0 ? "stm" : null;
    case "8": return uf ? `tj${uf === "df" ? "dft" : uf}` : null;
    case "9": return ({ 13: "tjmmg", 21: "tjmrs", 26: "tjmsp" } as Record<number, string>)[tr] ?? null;
    default: return null; // 1 = STF, 2 = CNJ
  }
}
