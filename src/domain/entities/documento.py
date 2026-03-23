# src/domain/entities/documento.py
# Entidade raiz do domínio: representa um documento jurídico

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Documento:
    """
    Entidade central do domínio — representa um documento jurídico a ser analisado.

    Attributes:
        texto:          Conteúdo textual extraído do documento
        nome:           Nome do arquivo ou identificador do documento
        tipo_extracao:  Como o texto foi obtido ('digital', 'escaneado', 'digitado')
        n_chars:        Número de caracteres extraídos (calculado automaticamente)
    """
    texto:         str
    nome:          str = "Documento"
    tipo_extracao: Optional[str] = None  # 'digital' | 'escaneado' | 'digitado'

    @property
    def n_chars(self) -> int:
        return len(self.texto)

    @property
    def n_palavras(self) -> int:
        return len(self.texto.split())

    @property
    def eh_valido(self) -> bool:
        """Documento com pelo menos 10 caracteres não-espaço."""
        return len(self.texto.strip()) >= 10
