# tests/infrastructure/test_metadados_extrator.py
# Bateria de testes unitários para o extrator robusto de metadados processuais (MetadadosExtrator).

import pytest
from src.infrastructure.nlp.metadados_extrator import MetadadosExtrator

@pytest.fixture
def extrator():
    return MetadadosExtrator()

class TestMetadadosExtratorCNJ:
    def test_cnj_formatado(self, extrator):
        texto = "Processo nº 1010384-26.2020.8.26.0002 em andamento."
        res = extrator.extrair(texto)
        assert res["numero_processo"] == "1010384-26.2020.8.26.0002"
        # Deve inferir o tribunal pelo processo
        assert res["tribunal"] == "TJSP"

    def test_cnj_apenas_numeros(self, extrator):
        texto = "Autos nº 10103842620208260002."
        res = extrator.extrair(texto)
        assert res["numero_processo"] == "1010384-26.2020.8.26.0002"
        assert res["tribunal"] == "TJSP"

    def test_cnj_stf(self, extrator):
        texto = "Processo STF: 0123456-12.2026.1.00.0000"
        res = extrator.extrair(texto)
        assert res["numero_processo"] == "0123456-12.2026.1.00.0000"
        assert res["tribunal"] == "STF"

    def test_cnj_stj(self, extrator):
        texto = "Processo STJ: 0123456-12.2026.3.00.0000"
        res = extrator.extrair(texto)
        assert res["numero_processo"] == "0123456-12.2026.3.00.0000"
        assert res["tribunal"] == "STJ"

    def test_cnj_nao_identificado(self, extrator):
        texto = "Não há processo citado aqui."
        res = extrator.extrair(texto)
        assert res["numero_processo"] == "Não identificado"
        assert res["tribunal"] == "Não identificado"

class TestMetadadosExtratorValorCausa:
    def test_valor_causa_termo_1(self, extrator):
        texto = "Dá-se à causa o valor de R$ 150.000,00."
        res = extrator.extrair(texto)
        assert res["valor_causa"] == "R$ 150.000,00"

    def test_valor_causa_termo_2(self, extrator):
        texto = "Atribui-se à causa o valor: R$ 5.430,50."
        res = extrator.extrair(texto)
        assert res["valor_causa"] == "R$ 5.430,50"

    def test_valor_causa_termo_3(self, extrator):
        texto = "Valor da Causa: 1.000.000"
        res = extrator.extrair(texto)
        assert res["valor_causa"] == "R$ 1.000.000"

    def test_valor_causa_nao_informado(self, extrator):
        texto = "Nenhum valor aqui."
        res = extrator.extrair(texto)
        assert res["valor_causa"] == "Não informado"

class TestMetadadosExtratorOAB:
    def test_oab_variacoes(self, extrator):
        texto = "Advogados: João Silva, OAB/SP 123.456, Maria Souza, OAB-RJ 78910, e Pedro, oab df 54321."
        res = extrator.extrair(texto)
        assert "OAB/SP 123.456" in res["advogados_oab"]
        assert "OAB/RJ 78910" in res["advogados_oab"]
        assert "OAB/DF 54321" in res["advogados_oab"]

    def test_oab_deduplicacao(self, extrator):
        texto = "OAB/SP 123.456 e depois OAB/SP 123.456 de novo."
        res = extrator.extrair(texto)
        assert res["advogados_oab"] == ["OAB/SP 123.456"]

class TestMetadadosExtratorDocumentos:
    def test_cpfs_e_cnpjs(self, extrator):
        texto = """
        Autor: CPF 123.456.789-01 (fictício) e Réu: CNPJ 12.345.678/0001-90.
        Outro CPF citado 123.456.789-01 duplicado.
        """
        res = extrator.extrair(texto)
        assert "123.456.789-01" in res["cpfs"]
        assert len(res["cpfs"]) == 1
        assert "12.345.678/0001-90" in res["cnpjs"]
        assert len(res["cnpjs"]) == 1

class TestMetadadosExtratorSigilo:
    def test_segredo_justica_positivo(self, extrator):
        texto = "Este processo tramita em segredo de justiça."
        res = extrator.extrair(texto)
        assert res["segredo_justica"] == "Sim"

    def test_segredo_justica_negativo(self, extrator):
        texto = "Petição inicial comum, autos públicos."
        res = extrator.extrair(texto)
        assert res["segredo_justica"] == "Não"

class TestMetadadosExtratorPartes:
    def test_extrair_partes(self, extrator):
        texto = """
        EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL.
        
        Autor: Caior Silva Santos (CPF 111.222.333-44)
        Réu: Grande Empresa de Tecnologia LTDA (CNPJ 11.222.333/0001-44)
        """
        res = extrator.extrair(texto)
        assert res["partes"].get("Autor") == "Caior Silva Santos"
        assert res["partes"].get("Réu") == "Grande Empresa de Tecnologia LTDA"

    def test_extrair_partes_variacoes(self, extrator):
        texto = """
        Requerente - Roberto Carlos
        Requerido: Banco Digital S.A.
        """
        res = extrator.extrair(texto)
        assert res["partes"].get("Autor") == "Roberto Carlos"
        assert res["partes"].get("Réu") == "Banco Digital S.A"

class TestMetadadosExtratorTribunalOrigem:
    def test_tribunal_por_texto_tjsp(self, extrator):
        texto = """
        TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO
        EGRÉGIO TRIBUNAL
        """
        res = extrator.extrair(texto)
        assert res["tribunal"] == "TJSP"

    def test_tribunal_por_texto_stf(self, extrator):
        texto = """
        SUPREMO TRIBUNAL FEDERAL
        """
        res = extrator.extrair(texto)
        assert res["tribunal"] == "STF"

class TestMetadadosExtratorComarca:
    def test_comarca_foro_de(self, extrator):
        texto = """
        TRIBUNAL DE JUSTIÇA
        FORO DE CAMPINAS
        """
        res = extrator.extrair(texto)
        assert res["comarca"] == "Campinas"

    def test_comarca_comarca_de(self, extrator):
        texto = """
        PODER JUDICIÁRIO DO ESTADO
        COMARCA DE BELO HORIZONTE
        """
        res = extrator.extrair(texto)
        assert res["comarca"] == "Belo Horizonte"

    def test_comarca_fallback_estado(self, extrator):
        texto = """
        TRIBUNAL DE JUSTIÇA DO ESTADO DE PERNAMBUCO
        """
        res = extrator.extrair(texto)
        # Deve inferir tribunal TJPE e usar PE como comarca fallback
        assert res["tribunal"] == "TJPE"
        assert res["comarca"] == "Pe"

class TestMetadadosExtratorDataAssinatura:
    def test_data_assinatura_final(self, extrator):
        texto = """
        Nestes termos, pede deferimento.
        São Paulo, 15 de maio de 2026.
        João Advogado
        """
        res = extrator.extrair(texto)
        assert res["data_documento"] == "15 de maio de 2026"
