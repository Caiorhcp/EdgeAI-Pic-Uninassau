# src/infrastructure/ocr/tesseract_extrator.py
# Adaptador de infraestrutura — OCR para PDFs escaneados (Tesseract)

from typing import BinaryIO, Dict

from src.domain.repositories.i_extrator_repository import IExtratorRepository
from src.shared.exceptions import OCRError
from src.shared.logger import get_logger

logger = get_logger(__name__)


class TesseractExtrator(IExtratorRepository):
    """
    Adaptador para extração de texto de PDFs escaneados usando Tesseract 5.
    Converte cada página para imagem PNG a 300 DPI e aplica OCR.
    """

    def detectar_tipo(self, arquivo: BinaryIO) -> str:
        """Delega detecção ao PDFPlumberExtrator — OCR não faz detecção sozinho."""
        return "escaneado"

    def extrair(self, arquivo: BinaryIO) -> Dict:
        """
        Aplica OCR em todas as páginas do PDF escaneado.

        Returns:
            Dict com texto completo, tipo 'escaneado' e metadados
        """
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
        except ImportError as exc:
            raise OCRError(
                "Dependências OCR não instaladas. "
                "Execute: pip install pytesseract pdf2image"
            ) from exc

        try:
            conteudo = arquivo.read()
            imagens = convert_from_bytes(conteudo, dpi=300)
        except Exception as exc:
            raise OCRError(f"Falha ao converter PDF para imagens: {exc}") from exc

        paginas = []
        for i, img in enumerate(imagens):
            try:
                texto = pytesseract.image_to_string(
                    img,
                    lang="por",
                    config="--oem 3 --psm 6",
                )
                if texto.strip():
                    paginas.append({
                        "pagina": i + 1,
                        "texto":  texto,
                        "chars":  len(texto),
                    })
            except Exception as exc:
                logger.warning("Falha ao processar página %d com OCR: %s", i + 1, exc)

        texto_completo = "\n\n".join(p["texto"] for p in paginas)
        paginas_com_texto = len(paginas)

        logger.info("OCR concluído: %d/%d páginas com texto", paginas_com_texto, len(imagens))
        return {
            "texto":  texto_completo,
            "tipo":   "escaneado",
            "meta": {
                "paginas":          len(imagens),
                "paginas_com_texto": paginas_com_texto,
                "metodo":           "Tesseract OCR",
            },
            "paginas": paginas,  # Dados por página para modo página-a-página
        }
