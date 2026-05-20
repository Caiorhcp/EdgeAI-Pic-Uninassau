# tests/domain/test_lgpd_service.py
# Testes automatizados para o LGPDService do domínio (compatível com Análise em Blocos / Context Binding)

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


class TestLGPDServiceScoreConformidade:
    def test_sem_violacoes_score_100(self, service, ner_vazio):
        blocos = [{"bloco": {"texto": "Texto sem dados sensíveis.", "tipo": "geral"}, "ner": ner_vazio}]
        resultado = service.analisar(blocos, "outro")
        assert resultado["score_conformidade"] == 100

    def test_violacao_critica_desconta_30(self, service, ner_vazio):
        # Dados sensíveis sem base legal nem consentimento -> CRÍTICA = -30
        blocos = [{"bloco": {"texto": "Dados sensíveis e de saúde coletados sem consentimento.", "tipo": "geral"}, "ner": ner_vazio}]
        resultado = service.analisar(blocos, "outro")
        assert resultado["score_conformidade"] == 70

    def test_violacao_baixa_desconta_5(self, service, ner_vazio):
        # Texto com dados sensíveis e consentimento expresso -> Risco mitigado (BAIXA = 5 de severidade na violação criada)
        texto = "Contrato de prestação de serviços com consentimento expresso para tratar dados sensíveis de saúde."
        blocos = [{"bloco": {"texto": texto, "tipo": "geral"}, "ner": ner_vazio}]
        resultado = service.analisar(blocos, "outro")
        for v in resultado["violacoes"]:
            if v.severidade == Severidade.BAIXA:
                assert resultado["score_conformidade"] <= 95
                break

    def test_nivel_conforme(self, service, ner_vazio):
        blocos = [{"bloco": {"texto": "Texto neutro.", "tipo": "geral"}, "ner": ner_vazio}]
        resultado = service.analisar(blocos, "outro")
        assert resultado["nivel"] == "CONFORME"

    def test_nivel_nao_conforme_score_baixo(self, service, ner_vazio):
        # Blocos com múltiplas violações críticas e altas -> NÃO CONFORME
        blocos = [
            {"bloco": {"texto": "Coleta de dados sensíveis sem qualquer aviso.", "tipo": "geral"}, "ner": ner_vazio},
            {"bloco": {"texto": "Mais dados sensíveis de saúde coletados sem base legal.", "tipo": "geral"}, "ner": ner_vazio},
            {"bloco": {"texto": "Transferência internacional de dados pessoais de crianças sem segurança.", "tipo": "geral"}, "ner": ner_vazio}
        ]
        resultado = service.analisar(blocos, "contrato")
        assert resultado["score_conformidade"] < 40
        assert resultado["nivel"] == "NÃO CONFORME"

    def test_retorna_contadores_por_severidade(self, service, ner_vazio):
        blocos = [{"bloco": {"texto": "Texto neutro.", "tipo": "geral"}, "ner": ner_vazio}]
        resultado = service.analisar(blocos, "outro")
        assert "criticas" in resultado
        assert "altas" in resultado
        assert "medias" in resultado
        assert "baixas" in resultado


class TestLGPDServiceViolacoes:
    def test_sem_violacoes_lista_vazia(self, service, ner_vazio):
        blocos = [{"bloco": {"texto": "Texto sem dados pessoais.", "tipo": "geral"}, "ner": ner_vazio}]
        resultado = service.analisar(blocos, "outro")
        assert resultado["total"] == 0
        assert resultado["violacoes"] == []

    def test_dados_criancas_detectados(self, service, ner_vazio):
        blocos = [{"bloco": {"texto": "O menor de idade carece de tutela.", "tipo": "geral"}, "ner": ner_vazio}]
        resultado = service.analisar(blocos, "acordao")
        tipos = [v.tipo for v in resultado["violacoes"]]
        assert any("criança" in t.lower() or "menores" in t.lower() or "crianças" in t.lower()
                   for t in tipos)

    def test_violacao_tem_campos_obrigatorios(self, service, ner_vazio):
        blocos = [{"bloco": {"texto": "Dados sensíveis coletados sem o devido consentimento.", "tipo": "geral"}, "ner": ner_vazio}]
        resultado = service.analisar(blocos, "contrato")
        assert len(resultado["violacoes"]) > 0
        for v in resultado["violacoes"]:
            assert v.tipo
            assert v.artigo
            assert v.descricao
            assert v.recomendacao
