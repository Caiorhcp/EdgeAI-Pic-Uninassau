# src/domain/repositories/i_classificador_repository.py
# Interface (porta) para o classificador de documentos

from abc import ABC, abstractmethod
from src.domain.value_objects.resultado_classificacao import ResultadoClassificacao


class IClassificadorRepository(ABC):
    """
    Porta de saída — define o contrato que qualquer implementação de
    classificador deve cumprir. Permite trocar TFLite por outro motor
    sem alterar a camada de aplicação.
    """

    @abstractmethod
    def classificar(self, texto: str) -> ResultadoClassificacao:
        """
        Classifica um texto jurídico e retorna o resultado.

        Args:
            texto: Texto pré-processado do documento

        Returns:
            ResultadoClassificacao com classe, confiança e probabilidades
        """
        ...
