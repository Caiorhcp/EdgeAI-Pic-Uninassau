# src/domain/repositories/i_extrator_repository.py
# Interface (porta) para extratores de texto (PDF / OCR)

from abc import ABC, abstractmethod
from typing import BinaryIO, Dict


class IExtratorRepository(ABC):
    """
    Porta de saída — contrato para qualquer extrator de texto.
    Permite substituir pdfplumber/Tesseract sem tocar na lógica de negócio.
    """

    @abstractmethod
    def extrair(self, arquivo: BinaryIO) -> Dict:
        """
        Extrai texto de um arquivo.

        Args:
            arquivo: File-like object do PDF ou imagem

        Returns:
            Dict com chaves:
                - texto: str — texto extraído completo
                - tipo:  str — 'digital' | 'escaneado'
                - meta:  dict — metadados (paginas, metodo, etc.)
        """
        ...

    @abstractmethod
    def detectar_tipo(self, arquivo: BinaryIO) -> str:
        """
        Detecta se o arquivo é PDF digital ou escaneado.

        Returns:
            'digital' ou 'escaneado'
        """
        ...
