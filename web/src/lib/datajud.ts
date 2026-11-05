import type { Cnj } from "./cnj";

// API Pública do Datajud (CNJ): https://datajud-wiki.cnj.jus.br/api-publica/
// Só traz metadados de processos públicos; partes e documentos não fazem parte da API.

const BASE = "https://api-publica.datajud.cnj.jus.br";
// Medido em nov/2026: o próprio Datajud leva 30–50 s por consulta ("took" no corpo da resposta).
const TIMEOUT_MS = 55_000;

export interface Movement {
  date: string;
  name: string;
  code: number | null; // código da Tabela Processual Unificada (TPU/CNJ); mais confiável que o nome
  details: string[]; // complementos tabelados, ex.: ["realizada", "instrução e julgamento"]
  body: string | null; // órgão julgador onde a movimentação ocorreu (muda em redistribuições)
}

export interface Instance {
  court: string;
  degree: string;
  className: string;
  subjects: string[];
  body: string;
  filedAt: string | null;
  system: string | null;
  updatedAt: string | null;
  movements: Movement[]; // todas, mais recentes primeiro
}

interface Source {
  tribunal?: string;
  grau?: string;
  classe?: { nome?: string };
  assuntos?: { nome?: string }[];
  orgaoJulgador?: { nome?: string };
  dataAjuizamento?: string;
  sistema?: { nome?: string };
  dataHoraUltimaAtualizacao?: string;
  movimentos?: {
    nome?: string;
    dataHora?: string;
    codigo?: number;
    complementosTabelados?: { nome?: string }[];
    orgaoJulgador?: { nome?: string };
  }[];
}

const DEGREES: Record<string, string> = {
  G1: "1º grau", G2: "2º grau", JE: "Juizado Especial", TR: "Turma Recursal", SUP: "Tribunal Superior",
};

export class DatajudError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

/** Uma entrada por grau de jurisdição em que o processo tramita; lista vazia se não encontrado. */
export async function fetchProcess(cnj: Cnj, alias: string): Promise<Instance[]> {
  const key = process.env.DATAJUD_API_KEY;
  if (!key) throw new DatajudError("Consulta indisponível: chave do Datajud não configurada no servidor.", 503);

  let res: Response;
  try {
    res = await fetch(`${BASE}/api_publica_${alias}/_search`, {
      method: "POST",
      headers: { Authorization: `APIKey ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({ query: { term: { numeroProcesso: cnj.digits } }, size: 10 }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: "no-store",
    });
  } catch {
    throw new DatajudError("O Datajud não respondeu a tempo. Tente novamente em instantes.", 504);
  }
  if (res.status === 401 || res.status === 403) {
    throw new DatajudError("O Datajud recusou a chave de acesso. A chave pública pode ter mudado.", 502);
  }
  if (res.status === 429) {
    throw new DatajudError("O Datajud limitou o número de consultas. Aguarde um minuto e tente de novo.", 429);
  }
  if (!res.ok) throw new DatajudError(`O Datajud respondeu com erro (${res.status}).`, 502);

  const data = (await res.json()) as { hits?: { hits?: { _source: Source }[] } };
  return (data.hits?.hits ?? []).map(({ _source: s }) => ({
    court: s.tribunal ?? alias.toUpperCase(),
    degree: DEGREES[s.grau ?? ""] ?? s.grau ?? "",
    className: s.classe?.nome ?? "",
    subjects: (s.assuntos ?? []).map((a) => a.nome).filter((n): n is string => !!n),
    body: s.orgaoJulgador?.nome ?? "",
    filedAt: s.dataAjuizamento ?? null,
    system: s.sistema?.nome ?? null,
    updatedAt: s.dataHoraUltimaAtualizacao ?? null,
    movements: (s.movimentos ?? [])
      .filter((m) => !!m.nome && !!m.dataHora)
      .sort((a, b) => b.dataHora!.localeCompare(a.dataHora!))
      .slice(0, 500) // processos longos passam de centenas; o limite só protege a resposta
      .map((m) => ({
        date: m.dataHora!,
        name: m.nome!,
        code: m.codigo ?? null,
        details: (m.complementosTabelados ?? []).map((c) => c.nome).filter((n): n is string => !!n),
        body: m.orgaoJulgador?.nome?.replace(/\s+/g, " ").trim() || null,
      })),
  }));
}
