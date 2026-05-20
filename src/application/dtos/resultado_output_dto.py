# src/application/dtos/resultado_output_dto.py
# DTO de saída — todos os dados que a interface (app.py) precisa consumir

from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional

from src.domain.value_objects.resultado_classificacao import ResultadoClassificacao


class ResultadoOutputDTO(BaseModel):
    """
    Data Transfer Object de saída — resultado completo da análise de um documento.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    classificacao:   ResultadoClassificacao
    resumo:          Dict[str, Any]
    relatorio_ner:   Dict[str, Any]
    analise_lgpd:    Dict[str, Any]
    texto:           str
    nome_doc:        str = "Documento"
    tipo_extracao:   Optional[str] = None
    metadados_arquivo: Optional[Dict[str, Any]] = None

    # ─── Atalhos para conveniência do app.py ──────────────────────────────────
    @property
    def classe(self) -> str:
        return self.classificacao.classe.value

    @property
    def confianca(self) -> float:
        return self.classificacao.confianca

    @property
    def probabilidades(self) -> Dict[str, float]:
        return self.classificacao.probabilidades

    @property
    def ms_inferencia(self) -> float:
        return self.classificacao.ms_inferencia

    @property
    def chars_extra(self) -> str:
        return f" · {len(self.texto):,} chars · {self.tipo_extracao or 'texto'}"
