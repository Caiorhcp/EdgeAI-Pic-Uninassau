# src/domain/entities/entidade_ner.py
# Entidade de domínio: representa uma entidade extraída por NER

from dataclasses import dataclass


@dataclass
class EntidadeNER:
    """
    Representa uma entidade jurídica extraída do texto.

    Attributes:
        tipo:       Categoria da entidade (CPF, CNPJ, OAB, TRIBUNAL, etc.)
        valor:      Texto extraído do documento
        inicio:     Índice de início no texto original
        fim:        Índice de fim no texto original
        risco_lgpd: True se a entidade é dado pessoal relevante para a LGPD
    """
    tipo:       str
    valor:      str
    inicio:     int
    fim:        int
    risco_lgpd: bool = False
