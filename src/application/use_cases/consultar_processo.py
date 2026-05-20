# src/application/use_cases/consultar_processo.py
# Use Case: consulta um processo judicial online e executa análise completa

from src.application.dtos.processo_input_dto import ProcessoInputDTO
from src.application.dtos.dados_processo_dto import DadosProcessoDTO
from src.application.dtos.documento_input_dto import DocumentoInputDTO
from src.application.dtos.resultado_output_dto import ResultadoOutputDTO
from src.application.use_cases.analisar_documento import AnalisarDocumentoUseCase
from src.domain.repositories.i_classificador_repository import IClassificadorRepository
from src.infrastructure.web.consultador_processo import ConsultadorProcesso
from src.shared.exceptions import DocumentoVazioError
from src.shared.logger import get_logger

logger = get_logger(__name__)


class ConsultarProcessoUseCase:
    """
    Use Case: Consulta um processo judicial pelo número CNJ e executa análise de IA.

    Fluxo:
    1. Consulta APIs públicas (STJ, STF, Datajud) buscando dados do processo
    2. Monta texto unificado a partir dos dados encontrados
    3. Passa para AnalisarDocumentoUseCase (classificação, NER, LGPD, resumo)
    4. Retorna dados do processo + resultado da análise

    Segue Dependency Injection.
    """

    def __init__(
        self,
        classificador: IClassificadorRepository,
        consultador: ConsultadorProcesso | None = None,
        analisar_doc_uc: AnalisarDocumentoUseCase | None = None,
    ):
        self._consultador    = consultador or ConsultadorProcesso()
        self._analisar_doc   = analisar_doc_uc or AnalisarDocumentoUseCase(classificador)

    def executar(
        self,
        dto: ProcessoInputDTO,
        n_frases_resumo: int = 4,
    ) -> tuple[DadosProcessoDTO, ResultadoOutputDTO | None]:
        """
        Executa a consulta e análise de um processo judicial.

        Args:
            dto: ProcessoInputDTO com o número CNJ
            n_frases_resumo: Número de frases no resumo (padrão 4)

        Returns:
            Tupla (DadosProcessoDTO, ResultadoOutputDTO | None)
            - Se o processo não for encontrado, ResultadoOutputDTO será None
            - Se o texto for muito curto para análise, ResultadoOutputDTO será None
        """
        logger.info("Consultando processo: %s", dto.numero_cnj)

        # 1. Buscar dados online
        dados = self._consultador.consultar(dto.numero_cnj)

        if not dados.encontrado:
            logger.warning("Processo não encontrado: %s", dto.numero_cnj)
            return dados, None

        # 2. Montar texto para análise
        texto_analise = dados.montar_texto_analise()
        if len(texto_analise.strip()) < 30:
            logger.warning("Texto do processo muito curto para análise: %d chars", len(texto_analise))
            dados.erro = "Dados do processo insuficientes para análise de IA."
            return dados, None

        logger.info(
            "Processo encontrado via %s — %d chars para análise",
            dados.fonte, len(texto_analise),
        )

        # 3. Executar análise de IA
        try:
            doc_dto = DocumentoInputDTO(
                texto=texto_analise,
                nome=f"Processo {dados.numero}",
                n_frases_resumo=n_frases_resumo,
            )
            resultado = self._analisar_doc.executar(doc_dto)
            return dados, resultado

        except DocumentoVazioError as exc:
            logger.warning("Documento vazio após montagem: %s", exc)
            dados.erro = str(exc)
            return dados, None

        except Exception as exc:
            logger.error("Erro inesperado na análise do processo: %s", exc)
            dados.erro = f"Erro interno na análise: {exc}"
            return dados, None

    def gerar_veredicto(
        self,
        dados: DadosProcessoDTO,
        resultado: ResultadoOutputDTO,
    ) -> dict:
        """
        Gera um 'veredicto' completo e detalhado em linguagem clara e acessível.

        Returns:
            Dict com: titulo, sintese, alertas[], recomendacoes[], nivel_risco,
                      detalhamento, cronologia
        """
        classe    = resultado.classe
        confianca = resultado.confianca
        score_lgpd = resultado.analise_lgpd.get("score_conformidade", 100)
        n_violacoes = resultado.analise_lgpd.get("total", 0)
        nivel_lgpd  = resultado.analise_lgpd.get("nivel", "")
        score_ner   = resultado.relatorio_ner.get("score_lgpd", 0)
        n_dados_pessoais = resultado.relatorio_ner.get("dados_pessoais", 0)
        resumo_texto = resultado.resumo.get("resumo", "")
        n_entidades = resultado.relatorio_ner.get("total_entidades", 0)

        # ─── Titulo ──────────────────────────────────────────────────────
        titulo = f"Analise Completa do Processo {dados.numero}"

        # ─── Sintese detalhada ───────────────────────────────────────────
        sintese_partes = []

        # Parágrafo 1: Identificação
        p1 = []
        if dados.classe_processual:
            p1.append(
                f"Trata-se de **{dados.classe_processual}**"
            )
            if dados.tribunal:
                p1.append(f"em tramitacao perante o **{dados.tribunal}**")
            if dados.comarca:
                p1.append(f"na comarca de **{dados.comarca}**")
            p1_text = " ".join(p1) + "."
            sintese_partes.append(p1_text)

        if dados.assunto:
            sintese_partes.append(
                f"O objeto da acao versa sobre **{dados.assunto}**."
            )

        # Parágrafo 2: Dados de tramitação
        p2 = []
        if dados.data_distribuicao:
            p2.append(f"O feito foi distribuido em **{dados.data_distribuicao}**")
        if dados.orgao_julgador:
            p2.append(f"e tramita perante o **{dados.orgao_julgador}**")
        if dados.relator:
            p2.append(f"sob relatoria do(a) **{dados.relator}**")
        if p2:
            sintese_partes.append(" ".join(p2) + ".")

        # Parágrafo 3: Status e situação atual
        if dados.status:
            status_lower = dados.status.lower()
            if "ativo" in status_lower:
                sintese_partes.append(
                    f"O processo encontra-se **EM ANDAMENTO** ({dados.status}), "
                    f"com movimentacoes registradas no sistema."
                )
            elif "baixado" in status_lower or "arquiv" in status_lower:
                sintese_partes.append(
                    f"O processo foi **BAIXADO/ARQUIVADO**, indicando encerramento "
                    f"da tramitacao nesta instancia."
                )
            elif "julgado" in status_lower or "definitivo" in status_lower:
                sintese_partes.append(
                    f"O processo possui decisao **DEFINITIVA** proferida, "
                    f"com julgamento de merito concluido."
                )
            elif "transitado" in status_lower:
                sintese_partes.append(
                    f"O processo **TRANSITOU EM JULGADO**, nao cabendo mais "
                    f"recurso ordinario contra a decisao proferida."
                )
            else:
                sintese_partes.append(f"Status atual do processo: **{dados.status}**.")

        # Parágrafo 4: Movimentações
        if dados.movimentos:
            n_movs = len(dados.movimentos)
            ultimo_mov = dados.movimentos[0] if dados.movimentos else ""
            sintese_partes.append(
                f"Foram identificadas **{n_movs} movimentacoes** no historico processual. "
                f"O andamento mais recente registrado foi: *{ultimo_mov}*."
            )

        # Parágrafo 5: Resumo da análise IA
        if resumo_texto:
            sintese_partes.append(f"**Resumo da analise automatizada:** {resumo_texto}")

        sintese = "\n\n".join(sintese_partes) or "Analise baseada nos dados disponiveis do processo."

        # ─── Detalhamento técnico ────────────────────────────────────────
        detalhamento_partes = []

        # Classificação pela IA
        detalhamento_partes.append(
            f"**Classificacao do documento:** O conteudo foi classificado como "
            f"**{classe}** com **{confianca:.1f}%** de confianca pelo modelo de IA Edge (TFLite INT8)."
        )

        # Entidades reconhecidas
        if n_entidades > 0:
            # score_ner é risco de exposição: 0 = sem risco, 100 = alto risco
            if score_ner == 0:
                risco_txt = "sem risco de exposicao"
            elif score_ner < 30:
                risco_txt = "risco baixo de exposicao"
            elif score_ner < 60:
                risco_txt = "risco moderado de exposicao"
            else:
                risco_txt = "risco alto de exposicao"
            detalhamento_partes.append(
                f"**Reconhecimento de entidades (NER):** Foram identificadas "
                f"**{n_entidades} entidades** no texto, incluindo "
                f"**{n_dados_pessoais} dado(s) pessoal(is)** protegido(s) pela LGPD "
                f"({risco_txt})."
            )

        # Conformidade LGPD
        detalhamento_partes.append(
            f"**Conformidade LGPD:** Score de conformidade: **{score_lgpd}/100** "
            f"(nivel: {nivel_lgpd or 'N/A'}). "
            f"{'Nenhuma violacao detectada.' if n_violacoes == 0 else f'{n_violacoes} violacao(oes) identificada(s).'}"
        )

        # Segredo de justiça
        if dados.segredo_justica == "Sim":
            detalhamento_partes.append(
                "**Sigilo processual:** Este processo tramita em **segredo de justica**, "
                "o que limita o acesso publico aos autos e requer tratamento especial dos dados."
            )

        detalhamento = "\n\n".join(detalhamento_partes)

        # ─── Cronologia resumida ─────────────────────────────────────────
        cronologia = ""
        if dados.movimentos and len(dados.movimentos) >= 2:
            datas = [m[:10] for m in dados.movimentos if len(m) >= 10 and m[4] == '-']
            if len(datas) >= 2:
                cronologia = (
                    f"O processo teve sua primeira movimentacao registrada em **{datas[-1]}** "
                    f"e a mais recente em **{datas[0]}**. "
                    f"Total de **{len(dados.movimentos)} andamentos** processados."
                )

        # ─── Alertas ─────────────────────────────────────────────────────
        alertas = []
        if n_dados_pessoais > 0:
            # Contextualizar: score_ner=0 é BOM (sem exposição)
            if score_ner == 0:
                alertas.append(
                    f"**{n_dados_pessoais} dado(s) pessoal(is)** identificado(s) "
                    f"no conteudo processual, porem **sem risco de exposicao**. "
                    f"Conformidade LGPD: {score_lgpd}/100."
                )
            else:
                alertas.append(
                    f"**{n_dados_pessoais} dado(s) pessoal(is)** identificado(s) "
                    f"com **risco de exposicao** detectado. "
                    f"Conformidade LGPD: {score_lgpd}/100."
                )
        if n_violacoes > 0:
            alertas.append(
                f"**{n_violacoes} violacao(oes) LGPD** detectada(s) - "
                f"conformidade: {score_lgpd}/100 ({nivel_lgpd})."
            )
        if dados.segredo_justica == "Sim":
            alertas.append(
                "Processo tramita em **segredo de justica** - dados sensiveis."
            )

        # ─── Recomendações contextuais ───────────────────────────────────
        recomendacoes = []
        if n_violacoes > 0:
            recomendacoes.append(
                "Revisar o tratamento de dados pessoais identificados no processo "
                "e garantir conformidade com a LGPD (Lei 13.709/2018)."
            )
        if classe in ("lgpd",):
            recomendacoes.append(
                "O documento trata de questoes de privacidade - "
                "recomenda-se consultar advogado especialista em LGPD."
            )
        if classe in ("peticao",):
            recomendacoes.append(
                "Verifique os prazos processuais vigentes e o status da citacao "
                "no portal do tribunal de origem."
            )
        if classe in ("acordao",):
            recomendacoes.append(
                "Verifique a existencia de recursos pendentes, embargos de declaracao "
                "e os efeitos vinculantes da decisao."
            )

        # Recomendações baseadas no status
        status_lower = (dados.status or "").lower()
        if "ativo" in status_lower:
            recomendacoes.append(
                "O processo esta em andamento. Acompanhe regularmente "
                "as movimentacoes no portal do tribunal."
            )
        elif "julgado" in status_lower or "definitivo" in status_lower:
            recomendacoes.append(
                "Decisao definitiva proferida. Verifique o prazo para interposicao "
                "de eventuais recursos (embargos, apelacao, recurso especial)."
            )
        elif "transitado" in status_lower:
            recomendacoes.append(
                "O processo transitou em julgado. A decisao e irrecorrivel "
                "e pode ser executada pela parte vencedora."
            )

        if not recomendacoes:
            recomendacoes.append(
                "Nenhuma irregularidade critica identificada na analise automatizada. "
                "Recomenda-se verificacao periodica dos andamentos."
            )

        # ─── Nível de risco ──────────────────────────────────────────────
        if score_lgpd < 40 or n_violacoes >= 3:
            nivel_risco = "ALTO"
        elif score_lgpd < 70 or n_violacoes >= 1:
            nivel_risco = "MEDIO"
        else:
            nivel_risco = "BAIXO"

        return {
            "titulo":           titulo,
            "sintese":          sintese,
            "alertas":          alertas,
            "recomendacoes":    recomendacoes,
            "nivel_risco":      nivel_risco,
            "classe_detectada": classe,
            "confianca":        confianca,
            "score_lgpd":       score_lgpd,
            "detalhamento":     detalhamento,
            "cronologia":       cronologia,
        }
