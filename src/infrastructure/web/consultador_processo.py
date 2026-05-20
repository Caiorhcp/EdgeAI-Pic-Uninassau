# src/infrastructure/web/consultador_processo.py
# Adaptador de infraestrutura — consulta de processos em APIs públicas (STJ, STF, Datajud)
# Todos os dados buscados são de domínio público conforme CF/88 art. 5 XIV e Lei 12.527/2011

import hashlib
import os
import re
import time
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from src.application.dtos.dados_processo_dto import DadosProcessoDTO
from src.shared.logger import get_logger

logger = get_logger(__name__)

# ─── Chave da API Pública do Datajud (CNJ) ────────────────────────────────────
# A chave é rotacionada periodicamente pelo CNJ.
# Obtenha a vigente em: https://datajud-wiki.cnj.jus.br/api-publica/acesso
# Configure via variável de ambiente DATAJUD_API_KEY ou arquivo .env
def _load_env_file():
    """Carrega variáveis de um arquivo .env na raiz do projeto (se existir)."""
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    env_path = os.path.normpath(env_path)
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key, value = key.strip(), value.strip()
                    if key and key not in os.environ:
                        os.environ[key] = value

_load_env_file()
DATAJUD_API_KEY = os.environ.get("DATAJUD_API_KEY", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; PIC-EdgeAI-UNISSAU/2.0; "
        "pesquisa academica juridica)"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
TIMEOUT = 15
DELAY   = 1.0  # respeito ao servidor

# ─── Regex para validar e decompor o número CNJ ──────────────────────────────
# Formato: NNNNNNN-DD.AAAA.J.TT.OOOO
_CNJ_REGEX = re.compile(
    r"^(\d{7})[\-\.](\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})$"
)


def normalizar_numero_cnj(numero: str) -> str:
    """Normaliza o número CNJ removendo espaços e padronizando separadores."""
    numero = numero.strip()
    # Aceitar com ou sem formatação
    apenas_digitos = re.sub(r"\D", "", numero)
    if len(apenas_digitos) == 20:
        # Formatar: NNNNNNN-DD.AAAA.J.TT.OOOO
        n = apenas_digitos
        return f"{n[:7]}-{n[7:9]}.{n[9:13]}.{n[13]}.{n[14:16]}.{n[16:20]}"
    return numero


def validar_numero_cnj(numero: str) -> bool:
    """Valida se o número está no formato CNJ correto."""
    numero_norm = normalizar_numero_cnj(numero)
    return bool(_CNJ_REGEX.match(numero_norm))


def detectar_tribunal(numero: str) -> str:
    """
    Detecta o tribunal pelo segmento J (justiça) e TT (tribunal) do número CNJ.
    J=1:STF/CNJ, J=2:TJ, J=3:TRF/JF, J=4:TRT, J=5:TSE/TRE, J=6:STM, J=7:STJ, J=8:TJ, J=9:Militar
    """
    norm = normalizar_numero_cnj(numero)
    m = _CNJ_REGEX.match(norm)
    if not m:
        return "DESCONHECIDO"
    segmento_j  = m.group(4)
    segmento_tt = m.group(5)

    mapa = {
        ("1", "00"): "STF",
        ("1", "01"): "CNJ",
        ("3", "00"): "STJ",
        ("3", "01"): "TRF1",
        ("3", "02"): "TRF2",
        ("3", "03"): "TRF3",
        ("3", "04"): "TRF4",
        ("3", "05"): "TRF5",
        ("3", "06"): "TRF6",
        ("4", "00"): "TST",
        ("5", "00"): "TSE",
        ("6", "00"): "STM",
        ("7", "00"): "STJ",
    }

    chave = (segmento_j, segmento_tt)
    if chave in mapa:
        return mapa[chave]

    # TJs estaduais (J=8)
    if segmento_j == "8":
        tj_mapa = {
            "01": "TJAC", "02": "TJAL", "03": "TJAP", "04": "TJAM",
            "05": "TJBA", "06": "TJCE", "07": "TJDF", "08": "TJES",
            "09": "TJGO", "10": "TJMA", "11": "TJMT", "12": "TJMS",
            "13": "TJMG", "14": "TJPA", "15": "TJPB", "16": "TJPR",
            "17": "TJPE", "18": "TJPI", "19": "TJRJ", "20": "TJRN",
            "21": "TJRS", "22": "TJRO", "23": "TJRR", "24": "TJSC",
            "25": "TJSE", "26": "TJSP", "27": "TJTO",
        }
        return tj_mapa.get(segmento_tt, f"TJ-{segmento_tt}")

    return f"J{segmento_j}-TT{segmento_tt}"


class ConsultadorProcesso:
    """
    Adaptador de infraestrutura para consulta de processos judiciais em APIs públicas.

    Estratégia de busca (fallback em cascata):
    1. API pública do STJ (para processos STJ)
    2. API pública do STF (para processos STF)
    3. API do Datajud/CNJ (portal nacional)
    4. Scraping do portal público do tribunal
    """

    def __init__(self, timeout: int = TIMEOUT):
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def consultar(self, numero_cnj: str) -> DadosProcessoDTO:
        """
        Consulta um processo judicial pelo número CNJ.

        Args:
            numero_cnj: Número do processo no formato CNJ

        Returns:
            DadosProcessoDTO com os dados encontrados (encontrado=False se não localizado)
        """
        numero_norm = normalizar_numero_cnj(numero_cnj)
        tribunal    = detectar_tribunal(numero_norm)

        logger.info("Consultando processo %s (tribunal: %s)", numero_norm, tribunal)

        # 1. STJ
        if tribunal in ("STJ",):
            result = self._buscar_stj(numero_norm)
            if result and result.encontrado:
                return result

        # 2. STF
        if tribunal in ("STF",):
            result = self._buscar_stf(numero_norm)
            if result and result.encontrado:
                return result

        # 3. Datajud (CNJ) — tenta para qualquer tribunal
        result = self._buscar_datajud(numero_norm, tribunal)
        if result and result.encontrado:
            return result

        # 4. Busca na jurisprudência do STJ/STF por número (processo pode constar em acórdão)
        result = self._buscar_jurisprudencia_stj(numero_norm)
        if result and result.encontrado:
            return result

        result = self._buscar_jurisprudencia_stf(numero_norm)
        if result and result.encontrado:
            return result

        # Não encontrado online
        if DATAJUD_API_KEY:
            # API Key configurada mas processo não existe no Datajud
            # Retornar honestamente "não encontrado" com links úteis
            logger.warning(
                "Processo %s nao encontrado em nenhuma fonte publica "
                "(STJ/STF/Datajud). O tribunal pode nao ter indexado este processo.",
                numero_norm,
            )

            # Links diretos de consulta manual por tribunal
            _portais = {
                "TJCE": "https://esaj.tjce.jus.br/cpopg/open.do",
                "TJSP": "https://esaj.tjsp.jus.br/cpopg/open.do",
                "TJRJ": "http://www4.tjrj.jus.br/ConsultaUnificada/consulta.do",
                "TJMG": "https://pje.tjmg.jus.br/pje/ConsultaPublica/listView.seam",
                "TJRS": "https://www.tjrs.jus.br/novo/busca/?return=proc",
                "TJPR": "https://portal.tjpr.jus.br/pesquisa_processual/",
                "TJBA": "https://esaj.tjba.jus.br/cpopg/open.do",
                "TJPE": "https://www.tjpe.jus.br/consultajurisprudenciaweb/",
                "TJSC": "https://esaj.tjsc.jus.br/cpopg/open.do",
                "TJGO": "https://pje.tjgo.jus.br/ConsultaPublica/listView.seam",
                "STJ":  "https://processo.stj.jus.br/processo/pesquisa/",
                "STF":  "https://portal.stf.jus.br/processos/",
            }
            portal = _portais.get(tribunal, "")
            link_msg = f"\n\nConsulte diretamente no portal do {tribunal}:\n{portal}" if portal else ""

            return DadosProcessoDTO(
                numero=numero_norm,
                tribunal=tribunal,
                encontrado=False,
                erro=(
                    f"Processo {numero_norm} nao foi encontrado nas bases publicas "
                    f"(STJ, STF, Datajud/CNJ). Possiveis motivos:\n"
                    f"- O {tribunal} ainda nao indexou este processo no Datajud\n"
                    f"- O processo pode estar apenas no e-SAJ ou PJe do tribunal\n"
                    f"- O numero CNJ pode estar incorreto\n"
                    f"- O processo tramita em segredo de justica"
                    f"{link_msg}"
                ),
                url_fonte=portal,
            )
        else:
            # Sem API Key — modo demonstrativo offline
            logger.warning(
                "[AVISO] Processo %s NAO encontrado (DATAJUD_API_KEY nao configurada). "
                "Ativando Modo Demonstrativo com dados ficticios.",
                numero_norm,
            )
            return self._buscar_mock_demonstrativo(numero_norm, tribunal)

    def _buscar_mock_demonstrativo(self, numero: str, tribunal: str) -> DadosProcessoDTO:
        """
        Gera dados processuais simulados ÚNICOS por número de processo.
        Usa hash do número CNJ para variar nomes, valores e datas, garantindo
        que dois processos diferentes nunca retornem dados idênticos.
        """
        logger.info("Gerando processo simulado (ÚNICO) para %s (%s)", numero, tribunal)

        # Gerar seed determinístico a partir do número do processo
        h = int(hashlib.md5(numero.encode()).hexdigest(), 16)

        # Pools de variação para gerar dados únicos
        _nomes_autores = [
            "João da Silva", "Maria Oliveira Santos", "Carlos Eduardo Pereira",
            "Ana Beatriz Costa", "Roberto Almeida Junior", "Fernanda Lima Souza",
            "Pedro Henrique Rocha", "Juliana Mendes Ferreira", "Lucas Gabriel Nunes",
            "Patrícia Ribeiro Campos", "André Luís Barbosa", "Camila Freitas Dias",
        ]
        _nomes_reus = [
            "E-Commerce Global S.A.", "Banco Digital do Brasil Ltda",
            "Construtora Horizonte S.A.", "Telecom Plus Operadora Ltda",
            "Supermercado Central Eireli", "Seguradora Nacional S.A.",
            "Distribuidora Norte Sul Ltda", "Financeira Crédito Fácil S.A.",
            "Transportadora Express Logística", "Indústria Alimentícia Sabor Ltda",
            "Imobiliária Lar Novo Empreendimentos", "Clínica Saúde Integral S.A.",
        ]
        _assuntos = [
            "Direito Civil / Responsabilidade Civil / Dano Moral",
            "Direito do Consumidor / Práticas Abusivas / Cobrança Indevida",
            "Direito Civil / Obrigações / Inadimplemento Contratual",
            "Direito Digital / Proteção de Dados / LGPD",
            "Direito Civil / Contratos / Rescisão Contratual",
            "Direito do Trabalho / Verbas Rescisórias",
            "Direito Tributário / Execução Fiscal / ICMS",
            "Direito Previdenciário / Benefício por Incapacidade",
        ]
        _classes = [
            "Procedimento Comum Cível", "Ação de Indenização",
            "Mandado de Segurança", "Ação Monitória",
            "Recurso de Apelação", "Embargos de Declaração",
            "Execução de Título Extrajudicial", "Ação Cautelar",
        ]
        _varas = [
            "1ª Vara Cível", "2ª Vara Cível", "3ª Vara Cível",
            "4ª Vara Cível", "1ª Vara do Trabalho", "Vara de Fazenda Pública",
            "Vara de Família e Sucessões", "Juizado Especial Cível",
        ]
        _juizes = [
            "Dr. Marcos Antônio de Lima", "Dra. Maria do Socorro Ferreira",
            "Dr. José Carlos Ribeiro", "Dra. Cláudia Helena Souza",
            "Dr. Fernando Augusto Pereira", "Dra. Renata Cristina Alves",
            "Dr. Paulo Roberto Costa", "Dra. Luciana Borges Menezes",
        ]
        _comarcas_tj = {
            "TJSP": ["São Paulo - SP", "Campinas - SP", "Ribeirão Preto - SP", "Santos - SP"],
            "TJRJ": ["Rio de Janeiro - RJ", "Niterói - RJ", "Petrópolis - RJ"],
            "TJMG": ["Belo Horizonte - MG", "Uberlândia - MG", "Juiz de Fora - MG"],
            "TJRS": ["Porto Alegre - RS", "Caxias do Sul - RS", "Pelotas - RS"],
            "TJPR": ["Curitiba - PR", "Londrina - PR", "Maringá - PR"],
            "TJPE": ["Recife - PE", "Olinda - PE", "Caruaru - PE"],
            "TJBA": ["Salvador - BA", "Feira de Santana - BA"],
            "TJCE": ["Fortaleza - CE", "Juazeiro do Norte - CE"],
        }

        # Selecionar dados com base no hash
        autor = _nomes_autores[h % len(_nomes_autores)]
        reu = _nomes_reus[(h >> 4) % len(_nomes_reus)]
        assunto = _assuntos[(h >> 8) % len(_assuntos)]
        classe = _classes[(h >> 12) % len(_classes)]
        vara = _varas[(h >> 16) % len(_varas)]
        juiz = _juizes[(h >> 20) % len(_juizes)]

        # Valor da causa variável
        valor_base = 5000 + (h % 200) * 500
        valor_causa = f"R$ {valor_base:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # Data variável
        dia = 1 + (h % 28)
        mes = 1 + ((h >> 5) % 12)
        data_dist = f"{dia:02d}/{mes:02d}/2026"

        # Comarca
        comarcas = _comarcas_tj.get(tribunal, ["Comarca não mapeada"])
        comarca = comarcas[(h >> 24) % len(comarcas)]

        segredo = "Sim" if (h % 7 == 0) else "Não"

        # Override para tribunais superiores
        if "STF" in tribunal:
            classe = "Recurso Extraordinário (RE)"
            vara = "Tribunal Pleno"
            comarca = "Brasília - DF"
            juiz = ["Min. Luís Roberto Barroso", "Min. Alexandre de Moraes",
                    "Min. Cármen Lúcia", "Min. Dias Toffoli"][(h >> 8) % 4]
        elif "STJ" in tribunal:
            classe = "Recurso Especial (REsp)"
            vara = f"{1 + (h % 4)}ª Turma"
            comarca = "Brasília - DF"
            juiz = ["Min. Nancy Andrighi", "Min. Herman Benjamin",
                    "Min. Og Fernandes", "Min. Benedito Gonçalves"][(h >> 8) % 4]

        return DadosProcessoDTO(
            numero=numero,
            tribunal=tribunal,
            assunto=assunto,
            classe_processual=classe,
            partes=[
                f"Autor: {autor}",
                f"Réu: {reu}",
            ],
            movimentos=[
                f"{data_dist} — Petição inicial protocolada",
                f"{dia + 3:02d}/{mes:02d}/2026 — Citação eletrônica expedida",
                f"{dia + 10:02d}/{mes:02d}/2026 — Contestação apresentada pelo réu",
            ],
            ementa=(
                f"{classe}. {assunto}. "
                f"Autor: {autor} em face de {reu}. "
                f"Valor da causa: {valor_causa}. "
                f"Processo distribuído à {vara} — {comarca}."
            ),
            texto_completo=(
                f"Excelentíssimo(a) Senhor(a) Doutor(a) Juiz(a) de Direito da {vara}. "
                f"{autor}, vem propor a presente ação ({classe}) em face de {reu}. "
                f"Assunto: {assunto}. "
                f"O(A) Autor(a) requer a condenação do(a) Réu ao pagamento de {valor_causa}. "
                f"Processo nº {numero}, distribuído em {data_dist}, "
                f"perante o {tribunal}, Comarca de {comarca}."
            ),
            fonte="[DEMO] Simulacao Local (Datajud indisponivel - configure DATAJUD_API_KEY)",
            url_fonte="https://datajud-wiki.cnj.jus.br/api-publica/acesso",
            encontrado=True,
            data_distribuicao=data_dist,
            valor_causa=valor_causa,
            segredo_justica=segredo,
            status="Em Andamento",
            orgao_julgador=vara,
            relator=juiz,
            comarca=comarca,
        )

    # ─── STJ ─────────────────────────────────────────────────────────────────

    def _buscar_stj(self, numero: str) -> Optional[DadosProcessoDTO]:
        """Busca processo no portal do STJ via API pública."""
        url = (
            "https://jurisprudencia.stj.jus.br/docs/api/search"
            f"?query={quote(numero)}&rows=5&start=0"
        )
        try:
            resp = self._session.get(url, timeout=self._timeout)
            if resp.status_code != 200:
                return None
            data = resp.json()
            docs = data.get("docs", [])
            if not docs:
                return None

            doc = docs[0]
            ementa = doc.get("ementa", "")
            decisao = doc.get("decisao", "")
            partes_raw = doc.get("partes", "")
            partes = [p.strip() for p in partes_raw.split(";") if p.strip()] if partes_raw else []

            texto = f"{ementa} {decisao}".strip()
            dto = DadosProcessoDTO(
                numero=numero,
                tribunal="STJ",
                assunto=doc.get("assunto", ""),
                classe_processual=doc.get("classe", ""),
                partes=partes,
                movimentos=[doc.get("orgao_julgador", "")] if doc.get("orgao_julgador") else [],
                ementa=ementa,
                texto_completo=texto,
                fonte="STJ — Jurisprudência",
                url_fonte=f"https://jurisprudencia.stj.jus.br/docs/api/search?query={quote(numero)}",
                encontrado=bool(texto),
                data_distribuicao=doc.get("data_decisao", "") or doc.get("data_publicacao", ""),
                valor_causa="Não informado",
                segredo_justica="Não",
                status="Julgado" if doc.get("data_decisao") else "Ativo",
                orgao_julgador=doc.get("orgao_julgador", ""),
                relator=doc.get("relator", ""),
                comarca="Brasília - DF"
            )
            logger.info("STJ: processo encontrado — %s", numero)
            return dto

        except Exception as exc:
            logger.warning("STJ busca falhou para %s: %s", numero, exc)
            return None

    def _buscar_jurisprudencia_stj(self, numero: str) -> Optional[DadosProcessoDTO]:
        """Busca o número do processo na jurisprudência do STJ (como referência em acórdão)."""
        # Número sem formatação para busca mais abrangente
        numero_simples = re.sub(r"\D", "", numero)
        url = (
            "https://jurisprudencia.stj.jus.br/docs/api/search"
            f"?query={quote(numero_simples)}&rows=3&start=0&tipo=acordao"
        )
        try:
            resp = self._session.get(url, timeout=self._timeout)
            if resp.status_code != 200:
                return None
            data = resp.json()
            docs = data.get("docs", [])
            if not docs:
                return None

            doc = docs[0]
            ementa = doc.get("ementa", "") or doc.get("decisao", "")
            if len(ementa) < 30:
                return None

            time.sleep(DELAY)
            return DadosProcessoDTO(
                numero=numero,
                tribunal="STJ",
                assunto=doc.get("assunto", "Não informado"),
                classe_processual=doc.get("classe", "Acórdão STJ"),
                partes=[doc.get("partes", "Partes não identificadas")],
                ementa=ementa,
                texto_completo=ementa,
                fonte="STJ — Acórdão relacionado",
                url_fonte="https://www.stj.jus.br/sites/portalp/Inicio",
                encontrado=True,
                data_distribuicao=doc.get("data_decisao", "") or doc.get("data_publicacao", ""),
                valor_causa="Não informado",
                segredo_justica="Não",
                status="Julgado",
                orgao_julgador=doc.get("orgao_julgador", "Turma Julgadora"),
                relator=doc.get("relator", ""),
                comarca="Brasília - DF"
            )
        except Exception as exc:
            logger.warning("STJ jurisprudência falhou: %s", exc)
            return None

    # ─── STF ─────────────────────────────────────────────────────────────────

    def _buscar_stf(self, numero: str) -> Optional[DadosProcessoDTO]:
        """Busca processo no portal do STF via API pública."""
        url = (
            "https://jurisprudencia.stf.jus.br/api/search/search"
            f"?query={quote(numero)}&pageSize=5&page=1"
        )
        try:
            resp = self._session.get(url, timeout=self._timeout, verify=False)
            if resp.status_code != 200:
                return None
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if not hits:
                return None

            src    = hits[0].get("_source", {})
            ementa = src.get("ementa", "")
            if not ementa:
                return None

            time.sleep(DELAY)
            return DadosProcessoDTO(
                numero=numero,
                tribunal="STF",
                assunto=src.get("assunto", ""),
                classe_processual=src.get("classe", ""),
                partes=[src.get("parteNome", "")] if src.get("parteNome") else [],
                ementa=ementa,
                texto_completo=ementa,
                fonte="STF — Jurisprudência",
                url_fonte="https://jurisprudencia.stf.jus.br",
                encontrado=True,
                data_distribuicao=src.get("dataAutuacao", "") or src.get("dataPublicacao", ""),
                valor_causa="Não informado",
                segredo_justica="Não",
                status="Julgado",
                orgao_julgador=src.get("orgaoJulgador", "") or "Tribunal Pleno",
                relator=src.get("relatorNome", ""),
                comarca="Brasília - DF"
            )
        except Exception as exc:
            logger.warning("STF busca falhou para %s: %s", numero, exc)
            return None

    def _buscar_jurisprudencia_stf(self, numero: str) -> Optional[DadosProcessoDTO]:
        """Busca referência ao processo na jurisprudência do STF."""
        numero_simples = re.sub(r"\D", "", numero)[:15]
        url = (
            "https://jurisprudencia.stf.jus.br/api/search/search"
            f"?query={quote(numero_simples)}&pageSize=3&page=1"
        )
        try:
            resp = self._session.get(url, timeout=self._timeout, verify=False)
            if resp.status_code != 200:
                return None
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if not hits:
                return None

            src    = hits[0].get("_source", {})
            ementa = src.get("ementa", "")
            if len(ementa) < 30:
                return None

            time.sleep(DELAY)
            return DadosProcessoDTO(
                numero=numero,
                tribunal="STF",
                assunto=src.get("assunto", "Não informado"),
                classe_processual=src.get("classe", "Acórdão STF"),
                partes=[src.get("parteNome", "")] if src.get("parteNome") else [],
                ementa=ementa,
                texto_completo=ementa,
                fonte="STF — Acórdão relacionado",
                url_fonte="https://jurisprudencia.stf.jus.br",
                encontrado=True,
                data_distribuicao=src.get("dataAutuacao", "") or src.get("dataPublicacao", ""),
                valor_causa="Não informado",
                segredo_justica="Não",
                status="Julgado",
                orgao_julgador=src.get("orgaoJulgador", "") or "Turma Julgadora",
                relator=src.get("relatorNome", ""),
                comarca="Brasília - DF"
            )
        except Exception as exc:
            logger.warning("STF jurisprudência falhou: %s", exc)
            return None

    # ─── Datajud / CNJ ───────────────────────────────────────────────────────

    def _buscar_datajud(self, numero: str, tribunal: str) -> Optional[DadosProcessoDTO]:
        """
        Consulta o Datajud (portal nacional do CNJ) via API ElasticSearch pública.
        Endpoint: https://datajud-wiki.cnj.jus.br/
        Requer header: Authorization: APIKey <chave>
        """
        # Mapeamento tribunal → índice Datajud
        _indices = {
            "STJ":  "stj",  "STF": "stf",
            "TJSP": "tjsp", "TJRJ": "tjrj", "TJMG": "tjmg",
            "TJRS": "tjrs", "TJPR": "tjpr", "TJBA": "tjba",
            "TJSC": "tjsc", "TJGO": "tjgo", "TJPE": "tjpe",
            "TJCE": "tjce", "TJDF": "tjdft", "TJES": "tjes",
            "TJMT": "tjmt", "TJMS": "tjms", "TJPA": "tjpa",
            "TJPB": "tjpb", "TJPI": "tjpi", "TJRN": "tjrn",
            "TJRO": "tjro", "TJRR": "tjrr", "TJSE": "tjse",
            "TJTO": "tjto", "TJAC": "tjac", "TJAL": "tjal",
            "TJAM": "tjam", "TJAP": "tjap", "TJMA": "tjma",
            "TRF1": "trf1", "TRF2": "trf2", "TRF3": "trf3",
            "TRF4": "trf4", "TRF5": "trf5", "TRF6": "trf6",
            "TST":  "tst",  "TSE": "tse",
        }
        indice = _indices.get(tribunal, "")

        # API pública do Datajud
        base_url = "https://api-publica.datajud.cnj.jus.br"

        if not indice:
            logger.warning("Datajud: tribunal '%s' sem índice mapeado.", tribunal)
            return None

        url = f"{base_url}/api_publica_{indice}/_search"
        numero_digits = re.sub(r"\D", "", numero)

        # Usar term query para busca exata pelo número
        payload = {
            "query": {
                "term": {
                    "numeroProcesso": numero_digits
                }
            },
            "size": 1,
        }

        try:
            datajud_headers = {**HEADERS, "Content-Type": "application/json"}
            if DATAJUD_API_KEY:
                datajud_headers["Authorization"] = f"APIKey {DATAJUD_API_KEY}"
            else:
                logger.warning(
                    "Datajud: DATAJUD_API_KEY não configurada. "
                    "A requisição provavelmente será rejeitada (HTTP 401)."
                )
            resp = self._session.post(
                url,
                json=payload,
                timeout=self._timeout,
                headers=datajud_headers,
            )
            if resp.status_code not in (200, 201):
                logger.warning("Datajud HTTP %d para %s", resp.status_code, numero)
                return None

            data  = resp.json()
            hits  = data.get("hits", {}).get("hits", [])
            if not hits:
                return None

            src = hits[0].get("_source", {})
            numero_proc = src.get("numeroProcesso", numero)

            # Classe processual: {codigo, nome}
            classe_raw = src.get("classe", {})
            classe = classe_raw.get("nome", "") if isinstance(classe_raw, dict) else str(classe_raw)

            # Assuntos: [{codigo, nome}]
            assuntos_raw = src.get("assuntos", [])
            assunto = assuntos_raw[0].get("nome", "") if assuntos_raw else ""

            # Partes (pode não existir em todos os tribunais)
            partes_raw = src.get("partes", [])
            partes = []
            for p in partes_raw:
                nome = p.get("nome", "")
                tipo = p.get("tipoParticipacao", "") or p.get("polo", "")
                if nome:
                    partes.append(f"{tipo} — {nome}".strip(" —"))

            # Movimentos: [{codigo, nome, dataHora, orgaoJulgador: {codigo, nome}}]
            movimentos_raw = src.get("movimentos", [])
            movimentos = [
                f"{m.get('dataHora', '')[:10]} — {m.get('nome', '')}"
                for m in movimentos_raw[:15]
                if m.get("nome")
            ]

            # Órgão julgador: {codigo, nome, codigoMunicipioIBGE}
            orgao_raw = src.get("orgaoJulgador", {})
            orgao_nome_full = orgao_raw.get("nome", "") if isinstance(orgao_raw, dict) else ""
            ibge_code = orgao_raw.get("codigoMunicipioIBGE", 0)

            # Grau de jurisdição
            grau_raw = src.get("grau", "")
            grau_map = {"G1": "1º Grau", "G2": "2º Grau", "TR": "Turma Recursal",
                        "SUP": "Superior", "RE": "Recursal"}
            grau = grau_map.get(grau_raw, grau_raw)

            # Separar vara/órgão de comarca no nome do órgão julgador
            # Padrões comuns:
            #   "1ª VARA CIVEL DA COMARCA DE AQUIRAZ"
            #   "Juízo Titular I - 5ª Vara Cível - Regional VII - Itaquera"
            #   "3ª TURMA RECURSAL - JUIZADO ESPECIAL DA FAZENDA PUBLICA"
            #   "Vara Única de Boqueirão"
            orgao_julgador = orgao_nome_full
            comarca = ""

            import re as _re
            # Padrão 1: "... DA COMARCA DE <cidade>"
            m_comarca = _re.search(r'(?:DA\s+)?COMARCA\s+DE\s+(.+)', orgao_nome_full, _re.IGNORECASE)
            if m_comarca:
                comarca = m_comarca.group(1).strip().title()
                # Órgão = parte antes de "DA COMARCA"
                idx = orgao_nome_full.upper().find("DA COMARCA")
                if idx > 0:
                    orgao_julgador = orgao_nome_full[:idx].strip().rstrip("-").strip()

            # Padrão 2: "... - Regional VII - <cidade>" (TJSP)
            if not comarca and " - " in orgao_nome_full:
                parts = [p.strip() for p in orgao_nome_full.split(" - ")]
                comarca = parts[-1]
                orgao_julgador = " - ".join(parts[:-1])

            # Padrão 3: "Vara Única de <cidade>"
            if not comarca:
                m_de = _re.search(r'(?:Vara\s+.+?)\s+[Dd][Ee]\s+(.+)', orgao_nome_full)
                if m_de:
                    comarca = m_de.group(1).strip().title()

            # Fallback: usar o tribunal
            if not comarca:
                comarca = tribunal_doc

            # Formatar nome do órgão julgador (title case se estiver ALL CAPS)
            if orgao_julgador and orgao_julgador == orgao_julgador.upper():
                orgao_julgador = orgao_julgador.title()

            # Data de ajuizamento: formato "20110826000000" → "26/08/2011"
            data_ajuiz = src.get("dataAjuizamento", "")
            data_formatada = ""
            if data_ajuiz and len(data_ajuiz) >= 8:
                try:
                    data_formatada = f"{data_ajuiz[6:8]}/{data_ajuiz[4:6]}/{data_ajuiz[:4]}"
                except (IndexError, ValueError):
                    data_formatada = data_ajuiz[:10]

            # Nível de sigilo: 0 = público, >0 = sigiloso
            nivel_sigilo = src.get("nivelSigilo", 0)
            segredo = "Sim" if nivel_sigilo and nivel_sigilo > 0 else "Não"

            # Tribunal
            tribunal_doc = src.get("tribunal", tribunal)

            # Sistema processual (PJe, Projudi, e-SAJ)
            sistema_raw = src.get("sistema", {})
            sistema_nome = sistema_raw.get("nome", "") if isinstance(sistema_raw, dict) else ""

            # Formato (Eletrônico, Físico)
            formato_raw = src.get("formato", {})
            formato_nome = formato_raw.get("nome", "") if isinstance(formato_raw, dict) else ""

            # Movimentos ordenados cronologicamente (mais recente primeiro)
            movimentos_raw = src.get("movimentos", [])
            movimentos_sorted = sorted(
                [m for m in movimentos_raw if m.get("nome")],
                key=lambda m: m.get("dataHora", ""),
                reverse=True
            )
            movimentos = [
                f"{m.get('dataHora', '')[:10]} — {m.get('nome', '')}"
                for m in movimentos_sorted[:20]
            ]

            # Montar texto para análise
            texto_parts = []
            if classe:
                texto_parts.append(f"{classe}.")
            if assunto:
                texto_parts.append(f"Assunto: {assunto}.")
            texto_parts.append(f"Tribunal: {tribunal_doc}.")
            if grau:
                texto_parts.append(f"Grau: {grau}.")
            if orgao_julgador:
                texto_parts.append(f"Orgao Julgador: {orgao_julgador}.")
            if comarca:
                texto_parts.append(f"Comarca: {comarca}.")
            if data_formatada:
                texto_parts.append(f"Data de Ajuizamento: {data_formatada}.")
            if partes:
                texto_parts.append(f"Partes: {', '.join(partes[:5])}.")
            if movimentos:
                texto_parts.append("Movimentos: " + " | ".join(movimentos[:8]) + ".")

            texto = " ".join(texto_parts)

            # Status inferido dos movimentos
            status = "Ativo"
            for m in movimentos:
                m_lower = m.lower()
                if "arquiv" in m_lower or "baix" in m_lower:
                    status = "Baixado"
                    break
                elif "definitivo" in m_lower:
                    status = "Julgado (Definitivo)"
                    break
                elif "transito em julgado" in m_lower or "trânsito em julgado" in m_lower:
                    status = "Transitado em Julgado"
                    break

            time.sleep(DELAY)
            logger.info("Datajud: processo %s encontrado com sucesso!", numero)
            return DadosProcessoDTO(
                numero=numero_proc or numero,
                tribunal=tribunal_doc,
                assunto=assunto,
                classe_processual=classe,
                partes=partes if partes else [f"Partes nao publicadas pelo {tribunal_doc}"],
                movimentos=movimentos,
                texto_completo=texto,
                fonte=f"Datajud - CNJ (Dados Reais) | {sistema_nome} | {formato_nome}",
                url_fonte="https://datajud-wiki.cnj.jus.br/",
                encontrado=bool(texto),
                data_distribuicao=data_formatada,
                valor_causa="",
                segredo_justica=segredo,
                status=status,
                orgao_julgador=orgao_julgador,
                relator="",
                comarca=comarca,
            )

        except Exception as exc:
            logger.warning("Datajud falhou para %s: %s", numero, exc)
            return None

