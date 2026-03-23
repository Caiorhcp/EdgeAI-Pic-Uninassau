# src/domain/value_objects/resultado_classificacao.py
# Value Object: resultado imutável de uma classificação

from dataclasses import dataclass
from typing import Dict

import numpy as np

from src.domain.value_objects.classe_documento import ClasseDocumento


@dataclass(frozen=True)
class ResultadoClassificacao:
    """
    Value Object imutável — resultado de uma inferência no modelo TFLite.

    Attributes:
        classe:         Classe com maior probabilidade
        confianca:      Probabilidade da classe vencedora (0-100)
        probabilidades: Dict {classe_str: prob_float} para todas as classes
        ms_inferencia:  Tempo gasto na inferência em milissegundos
    """
    classe:         ClasseDocumento
    confianca:      float
    probabilidades: Dict[str, float]
    ms_inferencia:  float

    @property
    def confianca_formatada(self) -> str:
        return f"{self.confianca:.1f}%"

    @property
    def nivel_confianca(self) -> str:
        if self.confianca >= 70:
            return "Alta confiança"
        elif self.confianca >= 40:
            return "Confiança moderada"
        return "Baixa confiança"

    def probs_ordenadas(self):
        """Retorna probabilidades ordenadas do maior para o menor."""
        return sorted(self.probabilidades.items(), key=lambda x: -x[1])
