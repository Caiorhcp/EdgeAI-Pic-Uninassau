# src/domain/entities/__init__.py
from src.domain.entities.documento import Documento
from src.domain.entities.entidade_ner import EntidadeNER
from src.domain.entities.violacao_lgpd import ViolacaoLGPD

__all__ = ["Documento", "EntidadeNER", "ViolacaoLGPD"]
