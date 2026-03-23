# src/sumarizador.py — sumarização extrativa edge (sem internet)
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ─── Pré-processamento ────────────────────────────────────────────────────────
def segmentar_frases(texto: str) -> list:
    """
    Divide o texto em frases limpas e relevantes.
    Remove cabeçalhos de página, frases muito curtas e linhas vazias.
    """
    # Remover marcadores de página
    texto = re.sub(r"\[Página \d+\]", "", texto)

    # Dividir por pontuação final
    frases = re.split(r"(?<=[.!?])\s+", texto)

    limpas = []
    for f in frases:
        f = f.strip()
        # Filtrar frases muito curtas ou sem conteúdo
        if len(f) < 30:
            continue
        # Filtrar frases que são só números/símbolos
        if len(re.sub(r"[^a-zA-ZÀ-ú]", "", f)) < 15:
            continue
        limpas.append(f)

    return limpas


# ─── Algoritmo de sumarização extrativa ──────────────────────────────────────
class SumarizadorJuridico:
    """
    Sumarização extrativa baseada em TF-IDF + similaridade de cosseno.

    Algoritmo:
    1. Segmenta o texto em frases
    2. Vetoriza cada frase com TF-IDF
    3. Calcula score de cada frase = média da similaridade com todas as outras
       (frases mais "centrais" no documento = mais importantes)
    4. Aplica bônus para frases com termos jurídicos relevantes
    5. Retorna as N frases com maior score
    """

    # Termos jurídicos que aumentam o score da frase
    TERMOS_IMPORTANTES = [
        # Decisão
        "decide", "decidiu", "acórdão", "sentença", "julgado", "unanimidade",
        "provido", "negado", "improvido", "procedente", "improcedente",
        # LGPD
        "dados pessoais", "tratamento", "titular", "controlador", "lgpd",
        "consentimento", "privacidade", "proteção de dados",
        # Contrato
        "contrato", "cláusula", "obriga", "rescisão", "pagamento", "prazo",
        "valor", "vigência", "partes",
        # Petição
        "requer", "pedido", "autor", "réu", "indenização", "danos",
        "excelentíssimo", "vem propor",
        # Legislação
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
        """Stopwords em português com adições jurídicas comuns."""
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
            # Jurídicos genéricos (não informativos)
            "presente", "referido", "mencionado", "supracitado",
        ]

    def _calcular_bonus(self, frase: str) -> float:
        """Bônus para frases com termos jurídicos importantes."""
        frase_lower = frase.lower()
        bonus = 0.0
        for termo in self.TERMOS_IMPORTANTES:
            if termo in frase_lower:
                bonus += 0.15
        return min(bonus, 0.6)  # máximo de 60% de bônus

    def sumarizar(self, texto: str, n_frases: int = 5) -> dict:
        """
        Gera um resumo extrativo do texto jurídico.

        Args:
            texto:    texto completo do documento
            n_frases: número de frases no resumo (default: 5)

        Returns:
            dict com resumo, frases selecionadas e metadados
        """
        frases = segmentar_frases(texto)

        if len(frases) == 0:
            return {
                "resumo": "Não foi possível extrair frases do documento.",
                "frases": [],
                "n_original": 0,
                "n_resumo": 0,
                "taxa_compressao": 0,
            }

        # Se o documento já é curto, retorna tudo
        if len(frases) <= n_frases:
            resumo = " ".join(frases)
            return {
                "resumo": resumo,
                "frases": frases,
                "n_original": len(frases),
                "n_resumo": len(frases),
                "taxa_compressao": 100.0,
            }

        # Vetorizar frases com TF-IDF
        try:
            from typing import Any as _Any
            _m: _Any = self.vectorizer.fit_transform(frases)
            # pyright: ignore[reportAttributeAccessIssue]
            matriz = getattr(_m, "toarray", lambda: _m)() if hasattr(_m, "toarray") else _m
        except Exception:
            # Fallback: pegar as primeiras n_frases
            frases_sel = frases[:n_frases]
            return {
                "resumo": " ".join(frases_sel),
                "frases": frases_sel,
                "n_original": len(frases),
                "n_resumo": len(frases_sel),
                "taxa_compressao": len(frases_sel) / len(frases) * 100,
            }

        # Calcular similaridade entre todas as frases
        sim_matrix = cosine_similarity(matriz)

        # Score de cada frase = média das similaridades com as demais
        scores = sim_matrix.mean(axis=1)

        # Aplicar bônus por termos jurídicos importantes
        for i, frase in enumerate(frases):
            scores[i] += self._calcular_bonus(frase)

        # Selecionar top N frases mantendo a ordem original do documento
        indices_top = np.argsort(scores)[-n_frases:]
        indices_ordenados = sorted(indices_top)

        frases_selecionadas = [frases[i] for i in indices_ordenados]
        resumo = " ".join(frases_selecionadas)

        return {
            "resumo":          resumo,
            "frases":          frases_selecionadas,
            "scores":          {frases[i]: float(scores[i]) for i in indices_ordenados},
            "n_original":      len(frases),
            "n_resumo":        len(frases_selecionadas),
            "taxa_compressao": len(frases_selecionadas) / len(frases) * 100,
        }

    def sumarizar_por_secao(self, texto: str, n_frases_por_secao: int = 2) -> dict:
        """
        Divide o documento em seções por página e sumariza cada uma.
        Útil para documentos longos com múltiplas páginas.
        """
        secoes = re.split(r"\[Página \d+\]", texto)
        secoes = [s.strip() for s in secoes if len(s.strip()) > 100]

        if not secoes:
            return self.sumarizar(texto)

        resumos_secoes = []
        for i, secao in enumerate(secoes):
            resultado = self.sumarizar(secao, n_frases=n_frases_por_secao)
            if resultado["resumo"]:
                resumos_secoes.append({
                    "secao":  i + 1,
                    "resumo": resultado["resumo"],
                    "frases": resultado["frases"],
                })

        resumo_geral = " ".join([s["resumo"] for s in resumos_secoes])

        return {
            "resumo":   resumo_geral,
            "secoes":   resumos_secoes,
            "n_secoes": len(resumos_secoes),
        }


# ─── Teste standalone ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    sumarizador = SumarizadorJuridico()

    textos_teste = [
        {
            "titulo": "Acórdão do STJ",
            "texto": """
            ACÓRDÃO. Vistos, relatados e discutidos estes autos, acordam os
            Ministros da Terceira Turma do Superior Tribunal de Justiça, na
            conformidade dos votos e das notas taquigráficas a seguir, por
            unanimidade, negar provimento ao recurso especial, nos termos do
            voto do Senhor Ministro Relator.
            Os Srs. Ministros votaram com o Sr. Ministro Relator.
            Brasília, 15 de março de 2024.
            O acórdão recorrido divergiu da orientação firmada por esta Corte
            Superior em casos análogos, razão pela qual merece reforma.
            A jurisprudência desta Corte é pacífica no sentido de que o prazo
            prescricional começa a fluir da data do conhecimento do dano pelo
            lesado, aplicando-se o princípio da actio nata.
            Incide o enunciado da Súmula 7 do STJ quando a pretensão recursal
            demanda reexame de provas, o que é vedado em recurso especial.
            O dano moral decorrente de inscrição indevida em cadastro de
            restrição ao crédito é presumido, dispensando prova do prejuízo.
            Por todo o exposto, nego provimento ao recurso especial.
            """
        },
        {
            "titulo": "Petição com LGPD",
            "texto": """
            Excelentíssimo Senhor Doutor Juiz de Direito da Vara Cível.
            O requerente, João Silva, CPF 123.456.789-09, por seu advogado,
            OAB/SP 98765, vem respeitosamente propor ação de indenização.
            A empresa ré tratou dados pessoais sensíveis do autor sem
            consentimento, violando o artigo 7 da Lei 13.709/2018 — LGPD.
            Os dados pessoais do requerente foram compartilhados com terceiros
            sem autorização, causando danos morais mensuráveis.
            O controlador tem o dever de garantir a segurança dos dados
            pessoais tratados, conforme artigo 46 da LGPD.
            Requer a condenação da ré ao pagamento de R$ 50.000,00 a título
            de danos morais, além da exclusão definitiva dos dados pessoais
            do requerente de todos os sistemas da empresa.
            Requer ainda a aplicação de multa diária em caso de descumprimento
            da ordem de exclusão dos dados pessoais.
            Dá-se à causa o valor de R$ 50.000,00.
            Nestes termos, pede deferimento.
            """
        },
    ]

    print("=" * 60)
    print("SUMARIZADOR JURÍDICO EDGE — Teste")
    print("=" * 60)

    for item in textos_teste:
        print(f"\n📄 {item['titulo']}")
        print("-" * 40)

        resultado = sumarizador.sumarizar(item["texto"], n_frases=3)

        print(f"Frases originais : {resultado['n_original']}")
        print(f"Frases no resumo : {resultado['n_resumo']}")
        print(f"Taxa de compressão: {100 - resultado['taxa_compressao']:.0f}% menor")
        print(f"\nRESUMO:")
        print(f"{resultado['resumo']}")

    print("\n" + "=" * 60)
    print("Sumarizador pronto para integração!")