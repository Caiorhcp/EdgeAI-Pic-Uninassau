# src/infrastructure/nlp/sumarizador.py
# Adaptador de infraestrutura — sumarização extrativa (TextRank simplificado)

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import spacy

from src.shared.logger import get_logger

logger = get_logger(__name__)

try:
    nlp = spacy.load("pt_core_news_sm", disable=["ner", "tagger", "lemmatizer"])
except OSError:
    nlp = None


def segmentar_frases(texto: str) -> list:
    """Divide o texto em frases limpas e relevantes."""
    texto = re.sub(r"\[Página \d+\]", "", texto)
    if nlp is not None and len(texto) < 100000:
        doc = nlp(texto)
        frases = [s.text.strip() for s in doc.sents if s.text.strip()]
    else:
        frases = re.split(r"(?<=[.!?])\s+", texto)
        
    limpas = []
    for f in frases:
        f = f.strip()
        if len(f) < 30:
            continue
        if len(re.sub(r"[^a-zA-ZÀ-ú]", "", f)) < 15:
            continue
        limpas.append(f)
    return limpas


class SumarizadorJuridico:
    """
    Sumarização extrativa baseada em TF-IDF + similaridade de cosseno.
    Implementa TextRank simplificado com bônus jurídico.
    """

    TERMOS_IMPORTANTES = [
        "decide", "decidiu", "acórdão", "sentença", "julgado", "unanimidade",
        "provido", "negado", "improvido", "procedente", "improcedente",
        "dados pessoais", "tratamento", "titular", "controlador", "lgpd",
        "consentimento", "privacidade", "proteção de dados",
        "contrato", "cláusula", "obriga", "rescisão", "pagamento", "prazo",
        "valor", "vigência", "partes",
        "requer", "pedido", "autor", "réu", "indenização", "danos",
        "excelentíssimo", "vem propor",
        "artigo", "lei", "código", "constituição", "súmula", "decreto",
    ]

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 2),
            min_df=1,
            stop_words=self._stopwords_juridicas(),
        )

    def _stopwords_juridicas(self) -> list:
        return [
            "de", "a", "o", "que", "e", "do", "da", "em", "um", "para",
            "com", "uma", "os", "no", "se", "na", "por", "mais", "as",
            "dos", "como", "mas", "ao", "ele", "das", "à", "seu", "sua",
            "ou", "quando", "muito", "nos", "já", "eu", "também", "só",
            "pelo", "pela", "até", "isso", "ela", "entre", "depois",
            "sem", "mesmo", "aos", "seus", "quem", "nas", "me", "esse",
            "eles", "você", "essa", "num", "nem", "suas", "meu", "às",
            "minha", "numa", "pelos", "elas", "havia", "seja", "qual",
            "será", "nós", "tenho", "lhe", "deles", "essas", "esses",
            "pelas", "este", "dele", "tu", "te", "vocês", "vos", "lhes",
            "meus", "minhas", "teu", "tua", "teus", "tuas", "nosso",
            "presente", "referido", "mencionado", "supracitado",
        ]

    def _calcular_bonus(self, frase: str) -> float:
        frase_lower = frase.lower()
        bonus = sum(0.15 for termo in self.TERMOS_IMPORTANTES if termo in frase_lower)
        return min(bonus, 0.6)

    def sumarizar(self, texto: str, n_frases: int = 5) -> dict:
        """Gera resumo extrativo do texto jurídico."""
        frases = segmentar_frases(texto)

        if len(frases) == 0:
            return {
                "resumo": "Não foi possível extrair frases do documento.",
                "frases": [], "n_original": 0, "n_resumo": 0, "taxa_compressao": 0,
            }

        if len(frases) <= n_frases:
            return {
                "resumo": " ".join(frases),
                "frases": frases,
                "n_original": len(frases), "n_resumo": len(frases),
                "taxa_compressao": 100.0,
            }

        try:
            from typing import Any, cast as _cast
            _tfidf_result: Any = self.vectorizer.fit_transform(frases)
            matriz = _tfidf_result.toarray()
        except Exception:
            frases_sel = frases[:n_frases]
            return {
                "resumo": " ".join(frases_sel),
                "frases": frases_sel,
                "n_original": len(frases), "n_resumo": len(frases_sel),
                "taxa_compressao": len(frases_sel) / len(frases) * 100,
            }

        sim_matrix = cosine_similarity(matriz)
        scores = sim_matrix.mean(axis=1)

        for i, frase in enumerate(frases):
            scores[i] += self._calcular_bonus(frase)

        indices_top = np.argsort(scores)[-n_frases:]
        indices_ordenados = sorted(indices_top)
        frases_selecionadas = [frases[i] for i in indices_ordenados]

        return {
            "resumo":          " ".join(frases_selecionadas),
            "frases":          frases_selecionadas,
            "scores":          {frases[i]: float(scores[i]) for i in indices_ordenados},
            "n_original":      len(frases),
            "n_resumo":        len(frases_selecionadas),
            "taxa_compressao": len(frases_selecionadas) / len(frases) * 100,
        }
