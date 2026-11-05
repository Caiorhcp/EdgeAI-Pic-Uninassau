// Consulta pública de cada tribunal, para o usuário baixar os autos e trazer o PDF ao S.A.P.O.
// Não há API pública de documentos: o download depende do sistema do tribunal (e, em geral, de login).
// Endereços abertos num navegador real em nov/2026, conferindo que a busca aparece. TJDFT, TJRJ, TJPR e TJGO
// ficaram de fora (página em branco, "acesso negado" ou fora do ar no teste) e caem na busca genérica.

import { courtOf, parseCnj } from "./cnj";

export interface Portal {
  court: string; // "TRF1"
  system: string; // "PJe", "eproc", "e-SAJ"...
  url: string;
  prefilled: boolean; // a página já abre com o número pesquisado
}

type Entry = { system: string; url: string | ((numero: string) => string); prefilled?: boolean };

const PJE = "PJe";
const ESAJ = "e-SAJ";

const PORTALS: Record<string, Entry> = {
  STF: { system: "Portal do STF", url: "https://portal.stf.jus.br/processos/" },
  STJ: { system: "Portal do STJ", url: "https://processo.stj.jus.br/processo/pesquisa/" }, // passa por verificação anti-robô
  TST: { system: "Portal do TST", url: "https://consultaprocessual.tst.jus.br/" },
  // O PJe novo do TRF1 é uma aplicação Angular: o antigo "listView.seam" abre em branco
  TRF1: { system: PJE, url: "https://pje1g-consultapublica.trf1.jus.br/consultapublica/ConsultaPublica/" },
  TRF2: { system: "eproc", url: "https://eproc-consulta.jfrj.jus.br/eproc/externo_controlador.php?acao=processo_consulta_publica" },
  TRF3: { system: PJE, url: "https://pje1g.trf3.jus.br/pje/ConsultaPublica/listView.seam" },
  TRF4: { system: "eproc", url: "https://consulta.trf4.jus.br/trf4/controlador.php?acao=consulta_processual_pesquisa" },
  TRF5: { system: PJE, url: "https://pje.trf5.jus.br/pjeconsulta/ConsultaPublica/listView.seam" },
  TRF6: { system: PJE, url: "https://pje1g.trf6.jus.br/consultapublica/ConsultaPublica/listView.seam" },
  TJSP: {
    system: ESAJ,
    prefilled: true,
    url: (n) => `https://esaj.tjsp.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado=${n}`,
  },
  TJAL: { system: ESAJ, url: "https://www2.tjal.jus.br/cpopg/open.do" },
  TJAM: { system: ESAJ, url: "https://consultasaj.tjam.jus.br/cpopg/open.do" },
  TJCE: { system: ESAJ, url: "https://esaj.tjce.jus.br/cpopg/open.do" },
  TJMS: { system: ESAJ, url: "https://esaj.tjms.jus.br/cpopg5/open.do" },
  TJBA: { system: PJE, url: "https://consultapublicapje.tjba.jus.br/pje/ConsultaPublica/listView.seam" },
  TJMG: { system: PJE, url: "https://pje-consulta-publica.tjmg.jus.br/" },
  TJPE: { system: PJE, url: "https://pje.cloud.tjpe.jus.br/1g/ConsultaPublica/listView.seam" },
  TJRS: { system: "Portal do TJRS", url: "https://www.tjrs.jus.br/novo/busca/?return=proc" }, // portal com o link "Consulta Processual"
  TJSC: { system: "eproc", url: "https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=processo_consulta_publica" },
};

/** Consulta pública do tribunal do processo, ou uma busca pela consulta quando o tribunal não está mapeado. */
export function portalFor(numero: string): Portal | null {
  const cnj = parseCnj(numero);
  const court = cnj && courtOf(numero);
  if (!cnj || !court) return null;

  // Justiça do Trabalho: PJe-JT de cada TRT aceita o número no endereço
  const trt = /^TRT(\d+)$/.exec(court);
  if (trt) {
    return { court, system: "PJe-JT", url: `https://pje.trt${trt[1]}.jus.br/consultaprocessual/detalhe-processo/${cnj.formatted}`, prefilled: true };
  }

  const entry = PORTALS[court];
  if (entry) {
    const url = typeof entry.url === "function" ? entry.url(cnj.formatted) : entry.url;
    return { court, system: entry.system, url, prefilled: !!entry.prefilled };
  }
  return {
    court,
    system: "consulta processual do tribunal",
    url: `https://www.google.com/search?q=${encodeURIComponent(`consulta processual pública ${court}`)}`,
    prefilled: false,
  };
}
