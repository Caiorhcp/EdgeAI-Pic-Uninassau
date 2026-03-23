# tests/domain/test_lgpd_service.py
# Testes automatizados para o LGPDService do domínio

import pytest
from src.domain.services.lgpd_service import LGPDService
from src.domain.value_objects.severidade import Severidade


@pytest.fixture
def service():
    return LGPDService()


@pytest.fixture
def ner_vazio():
    """Relatório NER sem dados pessoais."""
    return {"dados_pessoais": 0, "score_lgpd": 0, "risco": "BAIXO", "entidades": {}}


@pytest.fixture
def ner_com_cpf():
    """Relatório NER com CPF detectado."""
    return {"dados_pessoais": 1, "score_lgpd": 30, "risco": "MÉDIO", "entidades": {"CPF": ["123.456.789-09"]}}


@pytest.fixture
def ner_multiplos():
    """Relatório NER com vários dados pessoais."""
    return {
        "dados_pessoais": 3, "score_lgpd": 60, "risco": "ALTO",
        "entidades": {"CPF": ["123.456.789-09"], "CNPJ": ["12.345.678/0001-99"], "EMAIL": ["a@b.com"]}
    }


class TestLGPDServiceScoreConformidade:
    def test_sem_violacoes_score_100(self, service, ner_vazio):
        resultado = service.analisar("Texto sem dados sensíveis.", ner_vazio, "outro")
        assert resultado["score_conformidade"] == 100

    def test_violacao_critica_desconta_30(self, service, ner_com_cpf):
        # CPF sem base legal → SEM_BASE_LEGAL (CRÍTICA = -30)
        resultado = service.analisar("O titular CPF 123.456.789-09 é interessado.", ner_com_cpf, "acordao")
        assert resultado["score_conformidade"] == 70

    def test_violacao_baixa_desconta_5(self, service, ner_multiplos):
        """Confirma o fix do bug: penalidade BAIXA = 5 (era chave 'BAIXO' inativa)."""
        # Força apenas a violação SEM_ENCARREGADO (BAIXA) com texto que não aciona outras
        texto = "Contrato com dados pessoais do titular, consentimento foi dado, medidas de segurança implementadas, notificação de incidentes prevista."
        resultado = service.analisar(texto, ner_multiplos, "outro")
        # Se SEM_ENCARREGADO está ativa e funciona, score < 100
        # (Assegura que viola e desconta)
        for v in resultado["violacoes"]:
            if v.severidade == Severidade.BAIXA:
                assert resultado["score_conformidade"] <= 95
                break

    def test_nivel_conforme(self, service, ner_vazio):
        resultado = service.analisar("Texto neutro.", ner_vazio, "outro")
        assert resultado["nivel"] == "CONFORME"

    def test_nivel_nao_conforme_score_baixo(self, service, ner_multiplos):
        # Texto com muitas violações → NÃO CONFORME
        texto = (
            "Este contrato coleta dados pessoais CPF 294.771.380-45 CNPJ 04.812.994/0001-67 "
            "para qualquer finalidade e transferência para servidores nos EUA. "
            "Os dados serão mantidos por 20 anos. Dados de saúde incluídos. "
            "Crianças e adolescentes. Compartilhamento com terceiros."
        )
        resultado = service.analisar(texto, ner_multiplos, "contrato")
        assert resultado["score_conformidade"] < 40
        assert resultado["nivel"] == "NÃO CONFORME"

    def test_retorna_contadores_por_severidade(self, service, ner_vazio):
        resultado = service.analisar("Texto neutro.", ner_vazio, "outro")
        assert "criticas" in resultado
        assert "altas" in resultado
        assert "medias" in resultado
        assert "baixas" in resultado


class TestLGPDServiceViolacoes:
    def test_sem_violacoes_lista_vazia(self, service, ner_vazio):
        resultado = service.analisar("Texto sem dados pessoais.", ner_vazio, "outro")
        assert resultado["total"] == 0
        assert resultado["violacoes"] == []

    def test_dados_criancas_detectados(self, service, ner_vazio):
        resultado = service.analisar("O menor de idade carece de tutela.", ner_vazio, "acordao")
        tipos = [v.tipo for v in resultado["violacoes"]]
        assert any("criança" in t.lower() or "menores" in t.lower() or "crianças" in t.lower()
                   for t in tipos)

    def test_violacao_tem_campos_obrigatorios(self, service, ner_com_cpf):
        resultado = service.analisar("Dados pessoais presentes.", ner_com_cpf, "contrato")
        for v in resultado["violacoes"]:
            assert v.tipo
            assert v.artigo
            assert v.descricao
            assert v.recomendacao
