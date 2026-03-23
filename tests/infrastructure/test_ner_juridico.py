# tests/infrastructure/test_ner_juridico.py
# Testes para o adaptador NER com validação matemática de CPF/CNPJ

import pytest
from src.infrastructure.nlp.ner_juridico import NERJuridico, _validar_cpf, _validar_cnpj


@pytest.fixture
def ner():
    return NERJuridico()


class TestValidacaoCPF:
    def test_cpf_valido(self):
        assert _validar_cpf("529.982.247-25") is True

    def test_cpf_invalido_sequencia(self):
        assert _validar_cpf("111.111.111-11") is False

    def test_cpf_invalido_digito_verificador(self):
        assert _validar_cpf("123.456.789-00") is False

    def test_cpf_valido_sem_pontuacao(self):
        assert _validar_cpf("52998224725") is True


class TestValidacaoCNPJ:
    def test_cnpj_valido(self):
        assert _validar_cnpj("11.222.333/0001-81") is True

    def test_cnpj_invalido_sequencia(self):
        assert _validar_cnpj("11.111.111/1111-11") is False

    def test_cnpj_invalido_digito(self):
        assert _validar_cnpj("12.345.678/0001-00") is False


class TestNERExtracaoBasica:
    def test_extrai_cpf_valido(self, ner):
        texto = "O titular CPF 529.982.247-25 solicitou acesso."
        entidades = ner.extrair(texto)
        cpfs = [e for e in entidades if e.tipo == "CPF"]
        assert len(cpfs) == 1
        assert "529" in cpfs[0].valor

    def test_nao_extrai_cpf_invalido(self, ner):
        """CPF com dígitos verificadores errados não deve ser extraído."""
        texto = "CPF 123.456.789-00 é inválido matematicamente."
        entidades = ner.extrair(texto)
        cpfs = [e for e in entidades if e.tipo == "CPF"]
        assert len(cpfs) == 0

    def test_extrai_cnpj_valido(self, ner):
        texto = "A empresa CNPJ 11.222.333/0001-81 contratou."
        entidades = ner.extrair(texto)
        cnpjs = [e for e in entidades if e.tipo == "CNPJ"]
        assert len(cnpjs) == 1

    def test_extrai_tribunal(self, ner):
        texto = "O STJ decidiu por unanimidade negar provimento."
        entidades = ner.extrair(texto)
        tribunais = [e for e in entidades if e.tipo == "TRIBUNAL"]
        assert len(tribunais) >= 1

    def test_extrai_valor_monetario(self, ner):
        texto = "O valor da causa é R$ 50.000,00."
        entidades = ner.extrair(texto)
        valores = [e for e in entidades if e.tipo == "VALOR_MONETARIO"]
        assert len(valores) >= 1

    def test_deduplicacao_cpf(self, ner):
        """Mesmo CPF mencionado duas vezes não deve aparecer duplicado."""
        texto = "CPF 529.982.247-25 e após verificação do CPF 529.982.247-25."
        entidades = ner.extrair(texto)
        cpfs = [e for e in entidades if e.tipo == "CPF"]
        assert len(cpfs) == 1

    def test_relatorio_retorna_estrutura_correta(self, ner):
        texto = "Titular CPF 529.982.247-25 solicitou dados."
        rel = ner.relatorio(texto)
        assert "total_entidades" in rel
        assert "dados_pessoais"  in rel
        assert "score_lgpd"      in rel
        assert "risco"           in rel
        assert "entidades"       in rel


class TestNERRiscoLGPD:
    def test_cpf_e_risco_lgpd(self, ner):
        texto = "Titular CPF 529.982.247-25."
        entidades = ner.extrair(texto)
        for e in entidades:
            if e.tipo == "CPF":
                assert e.risco_lgpd is True

    def test_tribunal_nao_e_risco_lgpd(self, ner):
        texto = "Acórdão do STJ reconheceu o direito."
        entidades = ner.extrair(texto)
        for e in entidades:
            if e.tipo == "TRIBUNAL":
                assert e.risco_lgpd is False
