# tests/domain/test_value_objects.py
# Testes para os Value Objects do domínio

import pytest
from src.domain.value_objects.classe_documento import ClasseDocumento
from src.domain.value_objects.severidade import Severidade


class TestClasseDocumento:
    def test_cinco_classes_existem(self):
        classes = [c.value for c in ClasseDocumento]
        assert "lgpd"     in classes
        assert "acordao"  in classes
        assert "contrato" in classes
        assert "peticao"  in classes
        assert "outro"    in classes

    def test_from_string(self):
        assert ClasseDocumento.from_string("lgpd")     == ClasseDocumento.LGPD
        assert ClasseDocumento.from_string("ACORDAO")  == ClasseDocumento.ACORDAO
        assert ClasseDocumento.from_string("desconhecido") == ClasseDocumento.OUTRO

    def test_tem_emoji(self):
        for c in ClasseDocumento:
            assert c.emoji, f"{c.value} deve ter emoji"

    def test_tem_descricao(self):
        assert "Dados" in ClasseDocumento.LGPD.descricao
        assert "Contrato" in ClasseDocumento.CONTRATO.descricao


class TestSeveridade:
    def test_quatro_niveis_existem(self):
        assert Severidade.CRITICA.value == "CRÍTICA"
        assert Severidade.ALTA.value    == "ALTA"
        assert Severidade.MEDIA.value   == "MÉDIA"
        assert Severidade.BAIXA.value   == "BAIXA"

    def test_penalidades_corretas(self):
        assert Severidade.CRITICA.penalidade == 30
        assert Severidade.ALTA.penalidade    == 20
        assert Severidade.MEDIA.penalidade   == 10
        assert Severidade.BAIXA.penalidade   ==  5  # FIX: era chave "BAIXO" inativa

    def test_icones_existem(self):
        for s in Severidade:
            assert s.icone, f"{s.value} deve ter ícone"
