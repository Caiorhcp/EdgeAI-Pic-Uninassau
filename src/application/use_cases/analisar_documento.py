# src/application/use_cases/analisar_documento.py
# Caso de uso principal — orquestra toda a análise de um documento jurídico

from src.application.dtos.documento_input_dto import DocumentoInputDTO
from src.application.dtos.resultado_output_dto import ResultadoOutputDTO
from src.domain.entities.documento import Documento
from src.domain.repositories.i_classificador_repository import IClassificadorRepository
from src.domain.services.lgpd_service import LGPDService
from src.infrastructure.nlp.ner_juridico import NERJuridico
from src.infrastructure.nlp.sumarizador import SumarizadorJuridico
from src.infrastructure.nlp.segmentador_juridico import SegmentadorJuridico
from src.infrastructure.nlp.metadados_extrator import MetadadosExtrator
from src.shared.exceptions import DocumentoVazioError
from src.shared.logger import get_logger

logger = get_logger(__name__)


class AnalisarDocumentoUseCase:
    """
    Caso de uso principal — Analysis of a single legal document.

    Recebe um DocumentoInputDTO e retorna um ResultadoOutputDTO.
    Orquestra (sem conter lógica de negócio):
        1. Classificação TFLite
        2. Sumarização extrativa
        3. Extração NER (entidades jurídicas)
        4. Análise de conformidade LGPD

    Segue Dependency Injection — recebe as dependências no construtor.
    """

    def __init__(
        self,
        classificador: IClassificadorRepository,
        ner:           NERJuridico | None         = None,
        sumarizador:   SumarizadorJuridico | None = None,
        lgpd_service:  LGPDService | None         = None,
        metadados_extrator: MetadadosExtrator | None = None,
    ):
        self._classificador = classificador
        _ner:         NERJuridico       = ner          or NERJuridico()
        _sumarizador: SumarizadorJuridico = sumarizador or SumarizadorJuridico()
        _lgpd:        LGPDService       = lgpd_service or LGPDService()
        _meta_ext:    MetadadosExtrator = metadados_extrator or MetadadosExtrator()
        self._segmentador = SegmentadorJuridico()
        self._ner         = _ner
        self._sumarizador = _sumarizador
        self._lgpd        = _lgpd
        self._meta_ext    = _meta_ext

    def executar(self, dto: DocumentoInputDTO) -> ResultadoOutputDTO:
        """
        Executa a análise completa do documento.

        Args:
            dto: DocumentoInputDTO com o texto e metadados

        Returns:
            ResultadoOutputDTO com todos os resultados

        Raises:
            DocumentoVazioError: Se o texto for muito curto para análise
        """
        documento = Documento(
            texto=dto.texto,
            nome=dto.nome,
            tipo_extracao=dto.tipo_extracao,
        )

        if not documento.eh_valido:
            raise DocumentoVazioError(
                f"Documento '{documento.nome}' está vazio ou muito curto."
            )

        logger.info("Analisando documento: %s (%d chars)", documento.nome, documento.n_chars)

        # 1. Classificação TFLite
        resultado_clf = self._classificador.classificar(documento.texto)
        logger.info(
            "Classificado como %s (%.1f%%) em %.3f ms",
            resultado_clf.classe.value,
            resultado_clf.confianca,
            resultado_clf.ms_inferencia,
        )

        # 2. Sumarização extrativa
        resumo = self._sumarizador.sumarizar(documento.texto, n_frases=dto.n_frases_resumo)

        # 3. Extração de entidades NER Globais
        relatorio_ner = self._ner.relatorio(documento.texto)
        logger.info(
            "NER: %d entidades (%d dados pessoais, score LGPD: %d/100)",
            relatorio_ner["total_entidades"],
            relatorio_ner["dados_pessoais"],
            relatorio_ner["score_lgpd"],
        )

        # 4. Análise LGPD em Blocos
        blocos = self._segmentador.segmentar(documento.texto)
        blocos_analisados = []
        for b in blocos:
            ner_bloco = self._ner.relatorio(b["texto"])
            blocos_analisados.append({
                "bloco": b,
                "ner": ner_bloco
            })
            
        analise_lgpd = self._lgpd.analisar(
            blocos_analisados,
            resultado_clf.classe.value,
        )
        logger.info(
            "LGPD: %d violação(ões) — conformidade %d/100 (%s) em %d blocos",
            analise_lgpd["total"],
            analise_lgpd["score_conformidade"],
            analise_lgpd["nivel"],
            len(blocos)
        )

        # 5. Extração de Metadados do Arquivo
        metadados_arquivo = self._meta_ext.extrair(documento.texto)

        return ResultadoOutputDTO(
            classificacao=resultado_clf,
            resumo=resumo,
            relatorio_ner=relatorio_ner,
            analise_lgpd=analise_lgpd,
            texto=documento.texto,
            nome_doc=documento.nome,
            tipo_extracao=documento.tipo_extracao,
            metadados_arquivo=metadados_arquivo,
        )
