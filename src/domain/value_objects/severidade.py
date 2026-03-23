# src/domain/value_objects/severidade.py
# Value Object: nível de severidade de uma violação LGPD

from enum import Enum


class Severidade(str, Enum):
    """
    Enum de severidade para violações LGPD.
    Herda de str para compatibilidade com serialização e comparações.
    """
    CRITICA = "CRÍTICA"
    ALTA    = "ALTA"
    MEDIA   = "MÉDIA"
    BAIXA   = "BAIXA"

    @property
    def penalidade(self) -> int:
        """Desconto no score de conformidade por violação desta severidade."""
        _PENALIDADES = {
            Severidade.CRITICA: 30,
            Severidade.ALTA:    20,
            Severidade.MEDIA:   10,
            Severidade.BAIXA:    5,
        }
        return _PENALIDADES[self]

    @property
    def icone(self) -> str:
        _ICONES = {
            Severidade.CRITICA: "🔴",
            Severidade.ALTA:    "🟠",
            Severidade.MEDIA:   "🟡",
            Severidade.BAIXA:   "🟢",
        }
        return _ICONES[self]
