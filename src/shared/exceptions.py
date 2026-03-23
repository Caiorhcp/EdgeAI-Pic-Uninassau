# src/shared/exceptions.py
# Exceções do domínio — hierarquia centralizada


class EdgeAIException(Exception):
    """Exceção base do projeto Edge AI Jurídico."""


# ─── Domínio ──────────────────────────────────────────────────────────────────

class DocumentoVazioError(EdgeAIException):
    """Levantada quando o texto extraído do documento está vazio."""


class ClassificacaoError(EdgeAIException):
    """Levantada quando a inferência no modelo falha."""


class ConformidadeLGPDError(EdgeAIException):
    """Levantada quando a análise LGPD não pode ser executada."""


# ─── Infraestrutura ───────────────────────────────────────────────────────────

class ModeloNaoEncontradoError(EdgeAIException):
    """Levantada quando o arquivo .tflite não é encontrado."""

    def __init__(self, path: str):
        super().__init__(
            f"Modelo TFLite não encontrado em: {path}\n"
            "Execute o pipeline de treino primeiro: python rodar_tudo.py"
        )


class ArtefatoNaoEncontradoError(EdgeAIException):
    """Levantada quando vectorizer.pkl ou encoder.pkl não existem."""

    def __init__(self, path: str):
        super().__init__(
            f"Artefato de pré-processamento não encontrado: {path}\n"
            "Execute: python pipeline/05_preprocessar.py"
        )


class PDFExtractionError(EdgeAIException):
    """Levantada quando não é possível extrair texto do PDF."""


class OCRError(EdgeAIException):
    """Levantada quando o Tesseract falha ou não está instalado."""
