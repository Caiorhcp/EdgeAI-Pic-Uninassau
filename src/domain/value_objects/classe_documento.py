# src/domain/value_objects/classe_documento.py
# Value Object: categorias de documentos jurídicos

from enum import Enum


class ClasseDocumento(str, Enum):
    """
    Enum das 5 classes de documentos jurídicos suportadas pelo modelo.
    Herda de str para compatibilidade com o LabelEncoder do scikit-learn.
    """
    LGPD     = "lgpd"
    ACORDAO  = "acordao"
    CONTRATO = "contrato"
    PETICAO  = "peticao"
    OUTRO    = "outro"

    @property
    def emoji(self) -> str:
        _EMOJIS = {
            ClasseDocumento.LGPD:     "🔒",
            ClasseDocumento.ACORDAO:  "⚖️",
            ClasseDocumento.CONTRATO: "📄",
            ClasseDocumento.PETICAO:  "📋",
            ClasseDocumento.OUTRO:    "📚",
        }
        return _EMOJIS[self]

    @property
    def descricao(self) -> str:
        _DESCRICOES = {
            ClasseDocumento.LGPD:     "Proteção de Dados Pessoais",
            ClasseDocumento.ACORDAO:  "Decisão Judicial / Acórdão",
            ClasseDocumento.CONTRATO: "Contrato / Instrumento Jurídico",
            ClasseDocumento.PETICAO:  "Petição / Requerimento Judicial",
            ClasseDocumento.OUTRO:    "Texto Jurídico Geral",
        }
        return _DESCRICOES[self]

    @property
    def cor_hex(self) -> str:
        _CORES = {
            ClasseDocumento.LGPD:     "#c084fc",
            ClasseDocumento.ACORDAO:  "#4aa3df",
            ClasseDocumento.CONTRATO: "#4ade80",
            ClasseDocumento.PETICAO:  "#fb923c",
            ClasseDocumento.OUTRO:    "#94a3b8",
        }
        return _CORES[self]

    @classmethod
    def from_string(cls, valor: str) -> "ClasseDocumento":
        """Converte string do LabelEncoder para o enum."""
        try:
            return cls(valor.lower())
        except ValueError:
            return cls.OUTRO
