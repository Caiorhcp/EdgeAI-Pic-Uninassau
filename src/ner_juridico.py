# src/ner_juridico.py
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict

# ─── Estrutura de uma entidade ────────────────────────────────────────────────
@dataclass
class Entidade:
    tipo:     str
    valor:    str
    inicio:   int
    fim:      int
    risco_lgpd: bool = False   # marca se é dado pessoal sensível

# ─── Padrões de extração ──────────────────────────────────────────────────────
PADROES = {

    # Dados pessoais — alto risco LGPD
    "CPF": {
        "regex": r"\b\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[-\.\s]?\d{2}\b",
        "lgpd": True,
        "descricao": "Cadastro de Pessoa Física"
    },
    "CNPJ": {
        "regex": r"\b\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\.\s]?\d{4}[-\.\s]?\d{2}\b",
        "lgpd": True,
        "descricao": "Cadastro Nacional de Pessoa Jurídica"
    },
    "OAB": {
        "regex": r"\bOAB[\/\s]?[A-Z]{2}[\/\s]?n?[oº°]?\s*[\d\.]+\b",
        "lgpd": False,
        "descricao": "Registro na Ordem dos Advogados"
    },
    "PROCESSO": {
        "regex": r"\b\d{7}[-\.\s]?\d{2}[\.\s]?\d{4}[\.\s]?\d{1}[\.\s]?\d{2}[\.\s]?\d{4}\b",
        "lgpd": False,
        "descricao": "Número de processo judicial (CNJ)"
    },

    # Valores e datas
    "VALOR_MONETARIO": {
        "regex": r"R\$\s*[\d\.]+[\,\d]*|\b[\d\.]+[\,\d]*\s*(?:reais|mil reais)\b",
        "lgpd": False,
        "descricao": "Valor monetário"
    },
    "DATA": {
        "regex": r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b|\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b",
        "lgpd": False,
        "descricao": "Data"
    },
    "PRAZO": {
        "regex": r"\b\d+\s+(?:dias?|meses?|anos?|horas?)\b",
        "lgpd": False,
        "descricao": "Prazo"
    },

    # Referências jurídicas
    "ARTIGO_LEI": {
        "regex": r"\bart(?:igo)?\.?\s*\d+[º°]?(?:[,\s]+(?:inciso|§|parágrafo)[\s\w°º]+)?\b",
        "lgpd": False,
        "descricao": "Referência a artigo de lei"
    },
    "LEI": {
        "regex": r"\b[Ll]ei\s+(?:[Nn]º?\.?\s*)?\d+[\./]\d+\b|\bLC\s+\d+\/\d+\b",
        "lgpd": False,
        "descricao": "Lei ou norma"
    },
    "TRIBUNAL": {
        "regex": r"\b(?:STF|STJ|TST|TSE|TRF|TRT|TJ[A-Z]{2}|CNJ|TJSP|TJRJ|TJMG)\b",
        "lgpd": False,
        "descricao": "Tribunal"
    },
    "SUMULA": {
        "regex": r"\bS[úu]mula\s+(?:Vinculante\s+)?n?[oº°]?\s*\d+\b",
        "lgpd": False,
        "descricao": "Súmula"
    },
}

# ─── Extrator principal ───────────────────────────────────────────────────────
class NERJuridico:

    def extrair(self, texto: str) -> List[Entidade]:
        entidades = []
        for tipo, config in PADROES.items():
            for m in re.finditer(config["regex"], texto, re.IGNORECASE):
                entidades.append(Entidade(
                    tipo=tipo,
                    valor=m.group().strip(),
                    inicio=m.start(),
                    fim=m.end(),
                    risco_lgpd=config["lgpd"]
                ))
        # Ordena por posição no texto
        return sorted(entidades, key=lambda e: e.inicio)

    def relatorio(self, texto: str) -> Dict:
        entidades = self.extrair(texto)

        agrupado = {}
        for e in entidades:
            if e.tipo not in agrupado:
                agrupado[e.tipo] = []
            if e.valor not in agrupado[e.tipo]:
                agrupado[e.tipo].append(e.valor)

        dados_pessoais = [e for e in entidades if e.risco_lgpd]
        score_lgpd     = min(100, len(dados_pessoais) * 25)

        return {
            "total_entidades": len(entidades),
            "dados_pessoais":  len(dados_pessoais),
            "score_lgpd":      score_lgpd,
            "risco":           "ALTO" if score_lgpd >= 75
                               else "MÉDIO" if score_lgpd >= 25
                               else "BAIXO",
            "entidades":       agrupado,
            "entidades_raw":   entidades,
        }

    def destacar(self, texto: str) -> str:
        """Retorna o texto com entidades marcadas entre colchetes."""
        entidades = self.extrair(texto)
        resultado = texto
        offset    = 0
        for e in entidades:
            marca  = f"[{e.tipo}: {e.valor}]"
            inicio = e.inicio + offset
            fim    = e.fim    + offset
            resultado = resultado[:inicio] + marca + resultado[fim:]
            offset   += len(marca) - (e.fim - e.inicio)
        return resultado


# ─── Teste direto ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ner = NERJuridico()

    textos_teste = [
        {
            "titulo": "Petição com dados pessoais",
            "texto": """
            Exmo. Sr. Juiz, João Silva, CPF 123.456.789-09, OAB/SP 98765,
            vem propor ação contra a empresa ACME LTDA, CNPJ 12.345.678/0001-99,
            conforme artigo 186 do Código Civil, Lei 10.406/2002.
            Processo nº 0001234-56.2024.8.26.0100.
            Dá-se à causa o valor de R$ 50.000,00.
            Prazo: 15 dias para contestação.
            """
        },
        {
            "titulo": "Acórdão do STJ",
            "texto": """
            ACÓRDÃO. STJ, 3ª Turma. Recurso Especial nº 1234567.
            Relator: Min. Antonio Silva. Julgado em 15 de março de 2024.
            Súmula 7 do STJ. Lei nº 13.709/2018 (LGPD).
            Artigo 105, inciso III, alínea a, da Constituição Federal.
            Por unanimidade, negado provimento. Honorários: R$ 3.000,00.
            """
        },
        {
            "titulo": "Contrato com dados sensíveis",
            "texto": """
            Contrato celebrado em 01/03/2024 entre as partes:
            Contratante: Maria Oliveira, CPF 987.654.321-00
            Contratada: TECH S.A., CNPJ 98.765.432/0001-10
            Valor: R$ 12.000,00 pagos em 12 meses.
            Prazo: 12 meses a partir da assinatura.
            Artigo 421 do Código Civil. Lei 13.709/2018.
            """
        },
    ]

    print("=" * 58)
    print("NER JURÍDICO — Extração de Entidades")
    print("=" * 58)

    for item in textos_teste:
        print(f"\n📄 {item['titulo']}")
        print("-" * 40)
        rel = ner.relatorio(item["texto"])

        print(f"  Total de entidades : {rel['total_entidades']}")
        print(f"  Dados pessoais     : {rel['dados_pessoais']}")
        print(f"  Score LGPD         : {rel['score_lgpd']}/100 — risco {rel['risco']}")
        print("\n  Entidades encontradas:")
        for tipo, valores in rel["entidades"].items():
            desc   = PADROES[tipo]["descricao"]
            lgpd   = " 🔒 LGPD" if PADROES[tipo]["lgpd"] else ""
            print(f"    [{tipo}]{lgpd}")
            for v in valores:
                print(f"      → {v}")

    print("\n" + "=" * 58)
    print("Módulo NER pronto para integração no app!")