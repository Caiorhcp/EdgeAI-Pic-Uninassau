// Marcos processuais a partir dos nomes de movimentação do Datajud (Tabelas Processuais Unificadas do CNJ).

export type Milestone = "Distribuição" | "Audiência" | "Decisão" | "Recurso" | "Trânsito em julgado" | "Baixa / arquivamento";

// Códigos TPU vistos em respostas reais do Datajud. O nome vem só como a folha da árvore
// ("Definitivo" em vez de "Arquivamento > Definitivo"), por isso o código vem antes do nome.
const CODES: Record<number, Milestone> = { 26: "Distribuição", 970: "Audiência", 246: "Baixa / arquivamento" };

// A ordem importa: "Trânsito em julgado" não pode virar "Decisão"
const RULES: [RegExp, Milestone][] = [
  [/trânsito em julgado/i, "Trânsito em julgado"],
  [/baixa definitiva|arquivamento definitivo|arquivad|^definitivo$/i, "Baixa / arquivamento"],
  [/ausência do autor à audiência/i, "Decisão"], // extinção sem resolução do mérito (Lei 9.099/95, art. 51, I)
  [/audiência/i, "Audiência"],
  [/distribuí|distribuiç|redistribu/i, "Distribuição"],
  [/procedência|improcedência|provimento|julgamento|extinç|homologaç|sentença|acórdão|liminar|tutela|concessão|denegaç|não conhecimento|admissibilidade/i, "Decisão"],
  [/recurso|apelaç|agravo|embargos/i, "Recurso"],
];

export function milestoneOf(movement: string, code?: number | null): Milestone | null {
  return (code != null ? CODES[code] : undefined) ?? RULES.find(([re]) => re.test(movement.trim()))?.[1] ?? null;
}

/** "Audiência (realizada; instrução e julgamento)", "Arquivamento definitivo" */
export function describeMovement(m: { name: string; code?: number | null; details?: string[] }): string {
  const name = m.code === 246 || /^definitivo$/i.test(m.name.trim()) ? "Arquivamento definitivo" : m.name;
  return m.details?.length ? `${name} (${m.details.join("; ")})` : name;
}

/** Mudanças de órgão julgador ao longo das movimentações (lista da mais nova para a mais antiga). */
export function redistributions(moves: { date: string; body: string | null }[]): { date: string; from: string; to: string }[] {
  const out: { date: string; from: string; to: string }[] = [];
  const chrono = [...moves].reverse().filter((m) => m.body);
  for (let i = 1; i < chrono.length; i++) {
    if (chrono[i].body !== chrono[i - 1].body) out.push({ date: chrono[i].date, from: chrono[i - 1].body!, to: chrono[i].body! });
  }
  return out;
}

/** Datajud usa ISO ("2024-03-14T10:00:00.000Z") ou compacto ("20240314100000"). */
export function parseDatajudDate(s: string | null): Date | null {
  if (!s) return null;
  const d = /^\d{14}$/.test(s) ? new Date(`${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}T00:00:00Z`) : new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function daysBetween(from: Date, to: Date): number {
  return Math.floor((to.getTime() - from.getTime()) / 86_400_000);
}

/** "3 anos e 2 meses", "45 dias" */
export function humanDuration(days: number): string {
  if (days < 60) return `${days} ${days === 1 ? "dia" : "dias"}`;
  const months = Math.floor(days / 30.44);
  if (months < 24) return `${months} meses`;
  const y = Math.floor(months / 12), m = months % 12;
  return `${y} anos${m ? ` e ${m} ${m === 1 ? "mês" : "meses"}` : ""}`;
}
