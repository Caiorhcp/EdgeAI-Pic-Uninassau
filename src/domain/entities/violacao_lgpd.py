# src/domain/entities/violacao_lgpd.py
# Entidade de domínio: representa uma violação LGPD detectada

from dataclasses import dataclass
from src.domain.value_objects.severidade import Severidade


@dataclass
class ViolacaoLGPD:
    """
    Representa uma violação da LGPD detectada em um documento.

    Attributes:
        tipo:         Nome descritivo da violação
        severidade:   Nível de risco (CRÍTICA, ALTA, MÉDIA, BAIXA)
        artigo:       Artigo da LGPD que embasa a violação
        descricao:    Descrição legível para o usuário
        evidencia:    Trecho do texto que gerou o alerta
        recomendacao: O que fazer para corrigir
    """
    tipo:         str
    severidade:   Severidade
    artigo:       str
    descricao:    str
    evidencia:    str
    recomendacao: str
