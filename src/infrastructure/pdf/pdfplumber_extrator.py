# src/infrastructure/pdf/pdfplumber_extrator.py
# Adaptador de infraestrutura — extração de texto de PDFs digitais (pdfplumber)

from typing import BinaryIO, Dict

import pdfplumber

from src.domain.repositories.i_extrator_repository import IExtratorRepository
from src.shared.exceptions import PDFExtractionError
from src.shared.logger import get_logger

logger = get_logger(__name__)

_MIN_CHARS_POR_PAGINA = 50  # Média abaixo deste valor → PDF escaneado


class PDFPlumberExtrator(IExtratorRepository):
    """
    Adaptador para extração de texto de PDFs digitais usando pdfplumber.
    Implementa IExtratorRepository.
    """

    def detectar_tipo(self, arquivo: BinaryIO) -> str:
        """
        Detecta se o PDF é digital (texto nativo) ou escaneado (apenas imagens).

        Returns:
            'digital' ou 'escaneado'
        """
        try:
            with pdfplumber.open(arquivo) as pdf:  # pyright: ignore
                paginas_amostra = pdf.pages[:3]
                if not paginas_amostra:
                    return "escaneado"

                chars_total = sum(
                    len(p.extract_text() or "") for p in paginas_amostra
                )
                media = chars_total / len(paginas_amostra)
                return "digital" if media >= _MIN_CHARS_POR_PAGINA else "escaneado"
        except Exception as exc:
            logger.warning("Erro ao detectar tipo de PDF: %s", exc)
            return "escaneado"

    def extrair(self, arquivo: BinaryIO) -> Dict:
        """
        Extrai texto de todas as páginas de um PDF digital.

        Returns:
            Dict com texto, tipo, e metadados (páginas, método)
        """
        try:
            paginas = []
            n_paginas = 0

            with pdfplumber.open(arquivo) as pdf:  # pyright: ignore
                n_paginas = len(pdf.pages)
                for i, pagina in enumerate(pdf.pages):
                    texto_pag = pagina.extract_text()
                    if texto_pag:
                        paginas.append(f"[Página {i + 1}]\n{texto_pag}")

            texto_completo = "\n\n".join(paginas)

            logger.info("Extraído texto de %d/%d páginas (pdfplumber)", len(paginas), n_paginas)
            return {
                "texto": texto_completo,
                "tipo":  "digital",
                "meta":  {"paginas": n_paginas, "metodo": "pdfplumber"},
            }
        except Exception as exc:
            raise PDFExtractionError(f"Falha ao extrair texto do PDF: {exc}") from exc

    def extrair_paginas(self, arquivo: BinaryIO) -> list:
        """
        Extrai texto página por página para análise individual.

        Returns:
            Lista de dicts {pagina, texto, n_chars}
        """
        resultado = []
        try:
            with pdfplumber.open(arquivo) as pdf:  # pyright: ignore
                for i, pagina in enumerate(pdf.pages):
                    texto = pagina.extract_text() or ""
                    if len(texto.strip()) > 20:
                        resultado.append({
                            "pagina": i + 1,
                            "texto":  texto,
                            "n_chars": len(texto),
                        })
        except Exception as exc:
            raise PDFExtractionError(f"Falha ao extrair páginas: {exc}") from exc

        return resultado
