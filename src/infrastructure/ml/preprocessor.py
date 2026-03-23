# src/infrastructure/ml/preprocessor.py
# Adaptador de infraestrutura — pré-processamento de texto para TF-IDF

import re

from src.shared.logger import get_logger

logger = get_logger(__name__)

# Regex pré-compilado para melhor performance
_PATTERN_CLEAN = re.compile(r"[^a-záàãâéêíóôõúüç\s]")
_PATTERN_SPACES = re.compile(r"\s+")


def limpar_texto(texto: str) -> str:
    """
    Normaliza texto para vetorização TF-IDF.

    Operações:
        1. Converte para minúsculas
        2. Remove tudo que não seja letra portuguesa ou espaço
        3. Colapsa múltiplos espaços em um único

    Args:
        texto: Texto bruto do documento

    Returns:
        Texto limpo e normalizado
    """
    texto = texto.lower()
    texto = _PATTERN_CLEAN.sub(" ", texto)
    texto = _PATTERN_SPACES.sub(" ", texto)
    return texto.strip()
