# src/application/use_cases/analisar_pdf.py
# Caso de uso — extrai texto de PDF (digital ou escaneado) e delega à análise

from typing import BinaryIO, List

from src.application.dtos.documento_input_dto import DocumentoInputDTO
from src.application.dtos.resultado_output_dto import ResultadoOutputDTO
from src.application.use_cases.analisar_documento import AnalisarDocumentoUseCase
from src.domain.repositories.i_classificador_repository import IClassificadorRepository
from src.infrastructure.ocr.tesseract_extrator import TesseractExtrator
from src.infrastructure.pdf.pdfplumber_extrator import PDFPlumberExtrator
from src.shared.exceptions import DocumentoVazioError, PDFExtractionError
from src.shared.logger import get_logger

logger = get_logger(__name__)


class AnalisarPDFUseCase:
    """
    Caso de uso para análise de arquivos PDF.
    Detecta automaticamente se o PDF é digital ou escaneado
    e delega a extração para o adaptador correto.

    Suporta dois modos:
        - Documento completo: une todas as páginas e analisa como um todo
        - Página por página: analisa cada página individualmente
    """

    def __init__(self, classificador: IClassificadorRepository):
        self._analisar_doc  = AnalisarDocumentoUseCase(classificador)
        self._pdf_extrator  = PDFPlumberExtrator()
        self._ocr_extrator  = TesseractExtrator()

    def detectar_tipo(self, arquivo: BinaryIO) -> str:
        """Detecta se o PDF é digital ou escaneado."""
        tipo = self._pdf_extrator.detectar_tipo(arquivo)
        arquivo.seek(0)
        return tipo

    def executar_completo(
        self,
        arquivo: BinaryIO,
        nome_arquivo: str,
        n_frases: int = 4,
    ) -> ResultadoOutputDTO:
        """
        Analisa o documento PDF inteiro como um único texto.

        Args:
            arquivo:      File-like object do PDF
            nome_arquivo: Nome do arquivo para o relatório
            n_frases:     Número de frases no resumo

        Returns:
            ResultadoOutputDTO com a análise completa
        """
        tipo = self._pdf_extrator.detectar_tipo(arquivo)
        arquivo.seek(0)

        if tipo == "digital":
            resultado_extracao = self._pdf_extrator.extrair(arquivo)
        else:
            resultado_extracao = self._ocr_extrator.extrair(arquivo)

        texto = resultado_extracao["texto"]
        meta  = resultado_extracao.get("meta", {})

        if len(texto.strip()) < 20:
            raise DocumentoVazioError(
                f"Não foi possível extrair texto suficiente de '{nome_arquivo}'."
            )

        chars_desc = f" · {len(texto):,} chars · {meta.get('metodo', tipo)}"

        dto = DocumentoInputDTO(
            texto=texto,
            nome=nome_arquivo,
            tipo_extracao=tipo,
            n_frases_resumo=n_frases,
        )
        return self._analisar_doc.executar(dto)

    def executar_por_pagina(
        self,
        arquivo: BinaryIO,
        nome_arquivo: str,
    ) -> List[dict]:
        """
        Analisa o PDF página por página.

        Returns:
            Lista de dicts com resultado + número de página por item
        """
        tipo = self._pdf_extrator.detectar_tipo(arquivo)
        arquivo.seek(0)

        if tipo == "digital":
            paginas = self._pdf_extrator.extrair_paginas(arquivo)
        else:
            resultado = self._ocr_extrator.extrair(arquivo)
            paginas = resultado.get("paginas", [])

        resultados = []
        for pag in paginas:
            texto = pag.get("texto", "")
            if len(texto.strip()) < 20:
                continue
            try:
                dto = DocumentoInputDTO(
                    texto=texto,
                    nome=f"{nome_arquivo} — Página {pag['pagina']}",
                    tipo_extracao=tipo,
                    n_frases_resumo=2,
                )
                resultado = self._analisar_doc.executar(dto)
                resultados.append({
                    "pagina":    pag["pagina"],
                    "resultado": resultado,
                })
            except DocumentoVazioError:
                continue

        return resultados
