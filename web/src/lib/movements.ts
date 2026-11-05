// Marcos processuais a partir dos nomes de movimentação do Datajud (Tabelas Processuais Unificadas do CNJ).

export type Milestone = "Distribuição" | "Audiência" | "Decisão" | "Recurso" | "Trânsito em julgado" | "Baixa / arquivamento";

// A ordem importa: "Trânsito em julgado" não pode virar "Decisão"
const RULES: [RegExp, Milestone][] = [
  [/trânsito em julgado/i, "Trânsito em julgado"],
  [/baixa definitiva|arquivamento definitivo|arquivad/i, "Baixa / arquivamento"],
  [/audiência/i, "Audiência"],
  [/distribuí|distribuiç|redistribu/i, "Distribuição"],
  [/procedência|improcedência|provimento|julgamento|extinç|homologaç|sentença|acórdão|liminar|tutela|concessão|denegaç|não conhecimento|admissibilidade/i, "Decisão"],
  [/recurso|apelaç|agravo|embargos/i, "Recurso"],
];

export function milestoneOf(movement: string): Milestone | null {
  return RULES.find(([re]) => re.test(movement))?.[1] ?? null;
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
