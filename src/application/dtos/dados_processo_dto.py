# src/application/dtos/dados_processo_dto.py
# DTO com dados estruturados de um processo judicial consultado online

from dataclasses import dataclass, field
from typing import List


@dataclass
class DadosProcessoDTO:
    """
    DTO com os dados extraídos de um processo judicial consultado online.

    Attributes:
        numero:             Número CNJ normalizado do processo
        tribunal:           Tribunal de origem (ex: STJ, TJSP)
        assunto:            Assunto/tema principal do processo
        classe_processual:  Classe processual (ex: Recurso Especial, Apelação)
        partes:             Lista de partes envolvidas (autor, réu, etc.)
        movimentos:         Histórico de movimentos/andamentos do processo
        ementa:             Ementa do acórdão, se disponível
        texto_completo:     Texto unificado para análise pela IA
        fonte:              Nome da fonte consultada (STJ, STF, Datajud)
        url_fonte:          URL da fonte para referência
        encontrado:         Se o processo foi encontrado (False = não encontrado)
        erro:               Mensagem de erro, se houver
        data_distribuicao:  Data de distribuição ou autuação
        valor_causa:        Valor da causa / valor econômico da ação
        segredo_justica:    Informa se tramita em segredo de justiça (Sim/Não)
        status:             Status do processo (ex: Ativo, Baixado, Suspenso)
        orgao_julgador:     Câmara, Turma ou Juízo julgador específico
        relator:            Ministro, Desembargador ou Juiz Relator
        comarca:            Comarca, Foro ou Cidade de tramitação
    """
    numero: str
    tribunal: str = ""
    assunto: str = ""
    classe_processual: str = ""
    partes: List[str] = field(default_factory=list)
    movimentos: List[str] = field(default_factory=list)
    ementa: str = ""
    texto_completo: str = ""
    fonte: str = ""
    url_fonte: str = ""
    encontrado: bool = False
    erro: str = ""
    data_distribuicao: str = ""
    valor_causa: str = ""
    segredo_justica: str = "Não"
    status: str = "Ativo"
    orgao_julgador: str = ""
    relator: str = ""
    comarca: str = ""

    def montar_texto_analise(self) -> str:
        """
        Monta um texto unificado, rico e detalhado para análise pela IA.
        Garante contexto completo com narrativa processual, mesmo com dados parciais.
        """
        secoes = []

        # ─── Cabeçalho identificador ─────────────────────────────────────
        cab = f"PROCESSO JUDICIAL N. {self.numero}"
        if self.tribunal:
            cab += f" — {self.tribunal}"
        secoes.append(cab)

        # ─── Identificação e Classificação ───────────────────────────────
        id_parts = []
        if self.classe_processual:
            id_parts.append(
                f"Classe Processual: {self.classe_processual}. "
                f"Trata-se de {self.classe_processual.lower()} em tramitação "
                f"perante o {self.tribunal or 'tribunal competente'}."
            )
        if self.assunto:
            id_parts.append(
                f"Assunto principal: {self.assunto}. "
                f"A matéria versa sobre {self.assunto.lower()}, "
                f"conforme classificação processual unificada do CNJ."
            )
        if id_parts:
            secoes.append("IDENTIFICACAO E CLASSIFICACAO: " + " ".join(id_parts))

        # ─── Dados de Tramitação ─────────────────────────────────────────
        tram_parts = []
        if self.data_distribuicao:
            tram_parts.append(f"Data de distribuicao/ajuizamento: {self.data_distribuicao}.")
        if self.orgao_julgador:
            tram_parts.append(f"Orgao julgador: {self.orgao_julgador}.")
        if self.comarca:
            tram_parts.append(f"Comarca/Foro: {self.comarca}.")
        if self.relator:
            tram_parts.append(f"Relator: {self.relator}.")
        if self.valor_causa:
            tram_parts.append(f"Valor da causa: {self.valor_causa}.")
        if self.segredo_justica:
            tram_parts.append(f"Segredo de justica: {self.segredo_justica}.")
        if self.status:
            tram_parts.append(f"Status atual: {self.status}.")
        if tram_parts:
            secoes.append("DADOS DE TRAMITACAO: " + " ".join(tram_parts))

        # ─── Partes envolvidas ───────────────────────────────────────────
        if self.partes:
            partes_txt = "; ".join(self.partes)
            secoes.append(f"PARTES ENVOLVIDAS: {partes_txt}.")

        # ─── Ementa ──────────────────────────────────────────────────────
        if self.ementa:
            secoes.append(f"EMENTA DO JULGADO: {self.ementa}")

        # ─── Histórico completo de movimentações ─────────────────────────
        if self.movimentos:
            mov_lines = []
            for i, m in enumerate(self.movimentos, 1):
                mov_lines.append(f"  {i}. {m}")
            secoes.append(
                f"HISTORICO DE MOVIMENTACOES ({len(self.movimentos)} andamentos registrados):\n"
                + "\n".join(mov_lines)
            )

            # Análise temporal
            datas = [m[:10] for m in self.movimentos if len(m) >= 10 and m[4] == '-']
            if len(datas) >= 2:
                mais_recente = datas[0]
                mais_antigo = datas[-1]
                secoes.append(
                    f"PERIODO DE TRAMITACAO: de {mais_antigo} a {mais_recente}. "
                    f"O processo possui {len(self.movimentos)} movimentacoes registradas."
                )

        # ─── Texto completo da fonte (ementa, jurisprudência) ────────────
        if self.texto_completo:
            secoes.append(f"TEXTO INTEGRAL DA FONTE: {self.texto_completo[:3000]}")

        # ─── Fonte dos dados ─────────────────────────────────────────────
        if self.fonte:
            secoes.append(f"FONTE DOS DADOS: {self.fonte}.")

        return "\n\n".join(secoes).strip()

