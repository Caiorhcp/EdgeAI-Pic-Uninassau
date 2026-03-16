# src/ner_juridico.py — v2.8 (Definitivo - Regex com Freio de Mão e Deduplicação Inteligente)
import re
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Entidade:
    tipo:       str
    valor:      str
    inicio:     int
    fim:        int
    risco_lgpd: bool = False

# ─── Funções de Validação ─────────────────────────────────────────────────────
def _apenas_digitos(v: str) -> str:
    return re.sub(r"\D", "", v)

def _validar_cpf(valor: str) -> bool:
    d = _apenas_digitos(valor)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for i in range(2):
        s = sum(int(d[j]) * (10 + i - j) for j in range(9 + i))
        esperado = (s * 10 % 11) % 10
        if int(d[9 + i]) != esperado:
            return False
    return True

def _validar_cnpj(valor: str) -> bool:
    d = _apenas_digitos(valor)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for pesos, pos in [(pesos1, 12), (pesos2, 13)]:
        s = sum(int(d[i]) * pesos[i] for i in range(pos))
        r = s % 11
        esperado = 0 if r < 2 else 11 - r
        if int(d[pos]) != esperado:
            return False
    return True

# ─── Padrões de Busca Atualizados ─────────────────────────────────────────────
PADROES = {
    # ── Novos Documentos (Para evitar falsos positivos de CPF) ──
    "CNH": {
        "regex": r"\b(?:CNH|Registro)\s*(?::|n[º°.]?)?\s*\d{11}\b",
        "lgpd": True,
        "descricao": "Carteira Nacional de Habilitação",
        "validar": None,
    },
    "RENAVAM": {
        "regex": r"\bRENAVAM\s*(?::|n[º°.]?)?\s*\d{11}\b",
        "lgpd": False,
        "descricao": "Registro Nacional de Veículos Automotores",
        "validar": None,
    },
    "PIS": {
        "regex": r"\b(?:PIS|NIS|PASEP)\s*(?::|n[º°.]?)?\s*\d{11}\b",
        "lgpd": True,
        "descricao": "PIS / NIS / PASEP",
        "validar": None,
    },

    # ── Dados pessoais — alto risco LGPD ──
    "CPF": {
        "regex": r"\b\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[-\.\s]?\d{2}\b|\b\d{11}\b",
        "lgpd": True,
        "descricao": "Cadastro de Pessoa Física",
        "validar": None,
    },
    "CNPJ": {
        "regex": r"\b\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\.\s]?\d{4}[-\.\s]?\d{2}\b",
        "lgpd": True,
        "descricao": "Cadastro Nacional de Pessoa Jurídica",
        "validar": None,
    },
    "RG": {
        "regex": r"\bRG\s*(?:n[º°.]?\s*)?[\d\.-]+\b",
        "lgpd": True,
        "descricao": "Registro Geral (Identidade)",
        "validar": None,
    },
    "EMAIL": {
        "regex": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "lgpd": True,
        "descricao": "Endereço de e-mail",
        "validar": None,
    },
    "TELEFONE": {
        "regex": r"(?:\(\+?55\s*\d{2}\)\s*|\+?55\s*\d{2}\s*|\(\d{2}\)\s+)(?:9\s*)?\d{4,5}[-\s]?\d{4}\b|\b(?:9\s*)?\d{4,5}-\d{4}\b",
        "lgpd": True,
        "descricao": "Número de telefone",
        "validar": None,
    },
    "ENDERECO": {
        # O Freio de Mão: Para no CEP, ou antes de palavras sensíveis (telefone, email, CPF) e fim de frase.
        "regex": r"\b(?:Rua|Av\.?|Avenida|Tv\.?|Travessa|Alameda|Al\.?|Rod(?:ovia)?|Praça|Pça\.?)\s+(?:.{2,150}?CEP:?\s*\d{5}[-\s]?\d{3}\b|(?:(?!\b(?:telefone|tel|e-mail|email|CPF|CNPJ|RG|inscrito|portador)\b|\.\s+[A-ZÀ-Ú]|\n).){5,120})",
        "lgpd": True,
        "descricao": "Endereço Completo",
        "validar": None,
    },

    # ── Documentos de veículo ──
    "PLACA_VEICULO": {
        "regex": r"\b(?!CTR-)[A-Z]{3}[-\s]?\d[A-Z0-9]\d{2}\b|\b(?!CTR-)[A-Z]{3}[-\s]?\d{4}\b",
        "lgpd": False,
        "descricao": "Placa de veículo (Mercosul ou antiga)",
        "validar": None,
    },

    # ── Identificação profissional ──
    "OAB": {
        "regex": r"\bOAB[\/\-\s]?[A-Z]{2}\s*n?[oº°.]?\s*[\d\.]+\b",
        "lgpd": False,
        "descricao": "Registro OAB",
        "validar": None,
    },
    "CRM": {
        "regex": r"\bCRM[\/\-\s]?[A-Z]{2}\s*n?[oº°.]?\s*[\d\.]+\b",
        "lgpd": False,
        "descricao": "Registro CRM (médico)",
        "validar": None,
    },

    # ── Processos e documentos judiciais ──
    "PROCESSO_CNJ": {
        "regex": r"\b\d{7}[-\.]?\d{2}[\.]\d{4}[\.]\d{1}[\.]\d{2}[\.]\d{4}\b",
        "lgpd": False,
        "descricao": "Número de processo judicial (CNJ)",
        "validar": None,
    },
    "PROCESSO_ANTIGO": {
        "regex": r"(?:(?:Proc(?:esso)?|Autos?|Feito)\s*n?[oº°.]?\s*)\d{4,6}[\/\-]\d{2,4}(?:\s*-\s*[A-Z]{2,})?",
        "lgpd": False,
        "descricao": "Número de processo (formato antigo)",
        "validar": None,
    },

    # ── Datas ──
    "DATA": {
        "regex": (
            r"\b(?:0?[1-9]|[12]\d|3[01])[\/\-](?:0?[1-9]|1[0-2])[\/\-]\d{2,4}\b"
            r"|\b\d{1,2}\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|"
            r"julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}\b"
        ),
        "lgpd": False,
        "descricao": "Data",
        "validar": None,
    },
    "DATA_EXTENSO": {
        "regex": (
            r"\b(?:primeiro|segundo|terceiro|"
            r"(?:vinte|trinta)(?:\s+e\s+"
            r"(?:um|dois|três|quatro|cinco|seis|sete|oito|nove))?|"
            r"(?:dez|onze|doze|treze|quatorze|quinze|dezesseis|dezessete|"
            r"dezoito|dezenove)|"
            r"(?:um|dois|três|quatro|cinco|seis|sete|oito|nove))\s+de\s+"
            r"(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|"
            r"setembro|outubro|novembro|dezembro)\s+de\s+"
            r"(?:dois\s+mil(?:\s+e\s+"
            r"(?:um|dois|três|quatro|cinco|seis|sete|oito|nove|dez|"
            r"onze|doze|treze|quatorze|quinze|dezesseis|dezessete|dezoito|dezenove|"
            r"vinte|trinta)(?:\s+e\s+"
            r"(?:um|dois|três|quatro|cinco|seis|sete|oito|nove))?)?|"
            r"mil\s+e\s+\w+(?:\s+e\s+\w+)*|\d{4})\b"
        ),
        "lgpd": False,
        "descricao": "Data por extenso",
        "validar": None,
    },

    # ── Valores e prazos ──
    "VALOR_MONETARIO": {
        "regex": r"R\$\s*[\d\.]+(?:,\d{2})?|\b[\d\.]+,\d{2}\s*(?:reais|mil reais)\b",
        "lgpd": False,
        "descricao": "Valor monetário",
        "validar": None,
    },
    "PRAZO": {
        "regex": r"\b\d+\s*(?:\([^)]+\))?\s*(?:dias?\s*úteis?|dias?\s*corridos?|dias?|meses?|anos?|horas?|semanas?)\b",
        "lgpd": False,
        "descricao": "Prazo",
        "validar": None,
    },

    # ── Referências jurídicas ──
    "LEI": {
        "regex": r"\b(?:Lei|LC|Decreto(?:-[Ll]ei)?)\s+(?:Complementar\s+)?(?:n[oº°.]?\s*)?[\d\.]+[\/\.]\d{2,5}(?:\/\d{2,4})?\b",
        "lgpd": False,
        "descricao": "Lei ou norma",
        "validar": None,
    },
    "ARTIGO_LEI": {
        "regex": r"\bart(?:igo)?\.?\s*\d+[º°]?(?:[,\s]+(?:inciso|§|parágrafo|alínea)(?:\s+[IVXivx\d]+[º°]?)?)?\b(?!\s*(?:da\s+)?[Ll]ei)",
        "lgpd": False,
        "descricao": "Referência a artigo de lei",
        "validar": None,
    },
    "TRIBUNAL": {
        "regex": r"\b(?:STF|STJ|TST|TSE|STM|TRF\s*\d?|TRT\s*\d+|TJ[A-Z]{2}|CNJ|CARF|TJSP|TJRJ|TJMG|TJRS|TJPR|TJBA)\b",
        "lgpd": False,
        "descricao": "Tribunal",
        "validar": None,
    },
    "SUMULA": {
        "regex": r"\bS[úu]mula\s+(?:Vinculante\s+)?n?[oº°.]?\s*\d+\b",
        "lgpd": False,
        "descricao": "Súmula",
        "validar": None,
    },
    "RECURSO": {
        "regex": r"\b(?:REsp|AgRg|HC|RHC|MS|RMS|ADI|ADPF|ADC|RE|AI|ARE|ACO|Rcl)\s*n?[oº°.]?\s*[\d\.]+\b",
        "lgpd": False,
        "descricao": "Número de recurso/ação",
        "validar": None,
    },

    # ── CEP ──
    "CEP": {
        "regex": r"\bCEP:?\s*\d{5}[-\s]?\d{3}\b",
        "lgpd": False,
        "descricao": "CEP",
        "validar": None,
    },
}

# ─── Prioridade para resolver sobreposições ───────────────────────────────────
PRIORIDADE = {
    "ENDERECO":        15,
    "PROCESSO_CNJ":    15,
    "CNH":             12,
    "RENAVAM":         12,
    "PIS":             12,
    "CEP":             10,
    "CPF":              8,
    "CNPJ":             8,
    "RG":               8,
    "EMAIL":            8,
    "TELEFONE":         7,
    "LEI":              7,
    "DATA":             6,
    "DATA_EXTENSO":     6,
    "PLACA_VEICULO":    5,
    "OAB":              4,
    "CRM":              4,
    "ARTIGO_LEI":       4,
    "RECURSO":          4,
    "PROCESSO_ANTIGO":  3,
    "VALOR_MONETARIO":  2,
    "PRAZO":            2,
    "TRIBUNAL":         1,
    "SUMULA":           1,
}

# ─── Extrator principal ───────────────────────────────────────────────────────
class NERJuridico:
    def _normalizar_ocr(self, texto: str) -> str:
        texto = re.sub(r"(?<=\d)O(?=\d)", "0", texto)
        texto = re.sub(r"(?<=\d)o(?=\d)", "0", texto)
        texto = re.sub(r"(?<=\d)l(?=\d)", "1", texto)
        return texto

    def _resolver_sobreposicoes(self, entidades: List[Entidade]) -> List[Entidade]:
        if not entidades:
            return entidades

        entidades = sorted(entidades, key=lambda e: (e.inicio, -PRIORIDADE.get(e.tipo, 0)))
        resultado = []
        ultimo_fim = -1

        for e in entidades:
            if e.inicio >= ultimo_fim:
                resultado.append(e)
                ultimo_fim = e.fim
            else:
                p_novo = PRIORIDADE.get(e.tipo, 0)
                p_anterior = PRIORIDADE.get(resultado[-1].tipo, 0)
                if p_novo > p_anterior:
                    resultado[-1] = e
                    ultimo_fim = e.fim

        return resultado

    def extrair(self, texto: str) -> List[Entidade]:
        texto_norm = self._normalizar_ocr(texto).replace('\n', ' ')

        todas = []
        for tipo, cfg in PADROES.items():
            for m in re.finditer(cfg["regex"], texto_norm, re.IGNORECASE | re.UNICODE):
                valor = m.group().strip(" ,.;")
                if cfg.get("validar") and not cfg["validar"](valor):
                    continue
                todas.append(Entidade(
                    tipo=tipo,
                    valor=valor,
                    inicio=m.start(),
                    fim=m.end(),
                    risco_lgpd=cfg["lgpd"],
                ))

        todas = sorted(todas, key=lambda e: e.inicio)
        todas = self._resolver_sobreposicoes(todas)

        vistos = set()
        unicas = []
        for e in todas:
            if e.tipo in ["CPF", "CNPJ", "TELEFONE", "CEP", "CNH", "RENAVAM", "PIS", "PROCESSO_CNJ"]:
                chave = (e.tipo, re.sub(r"\D", "", e.valor))
            else:
                chave = (e.tipo, e.valor.strip().lower())
                
            if chave not in vistos:
                vistos.add(chave)
                unicas.append(e)

        return unicas

    def relatorio(self, texto: str) -> Dict:
        entidades = self.extrair(texto)

        agrupado: Dict[str, List[str]] = {}
        for e in entidades:
            agrupado.setdefault(e.tipo, [])
            if e.valor not in agrupado[e.tipo]:
                agrupado[e.tipo].append(e.valor)

        dados_pessoais = [e for e in entidades if e.risco_lgpd]

        pesos = {
            "CPF":           30,
            "CNPJ":          20,
            "RG":            20,
            "CNH":           20,
            "PIS":           15,
            "EMAIL":         20,
            "TELEFONE":      15,
            "ENDERECO":      10,
            "PLACA_VEICULO":  5,
        }
        score = sum(pesos[t] for t in pesos if t in {e.tipo for e in dados_pessoais})
        score = min(score, 100)

        return {
            "total_entidades": len(entidades),
            "dados_pessoais":  len(dados_pessoais),
            "score_lgpd":      score,
            "risco": "ALTO"  if score >= 50 else "MÉDIO" if score >= 20 else "BAIXO",
            "entidades":       agrupado,
            "entidades_raw":   entidades,
        }

    def destacar(self, texto: str) -> str:
        entidades = self.extrair(texto)
        resultado = texto
        offset = 0
        for e in entidades:
            marca = f"[{e.tipo}: {e.valor}]"
            inicio = e.inicio + offset
            fim = e.fim + offset
            resultado = resultado[:inicio] + marca + resultado[fim:]
            offset += len(marca) - (e.fim - e.inicio)
        return resultado


# ─── Teste ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ner = NERJuridico()

    TEXTO_ROBUSTO = """DOCUMENTO FICTÍCIO PARA TESTE INTENSIVO DE NER
TERMO DE REPRESENTAÇÃO ADMINISTRATIVA, RELATÓRIO PRELIMINAR E COMUNICAÇÃO DE POSSÍVEL ILÍCITO CIVIL, PENAL E ADMINISTRATIVO
Aos vinte e três (23) dias do mês de maio do ano de dois mil e vinte e três (2023), às 14h37min, na sede da Promotoria de Justiça da Comarca de Fortaleza/CE, situada na Rua Assunção, nº 1100, Centro, Fortaleza/CE, CEP 60050-010, compareceu espontaneamente o Sr. Carlos Henrique Almeida Pereira, brasileiro, casado, analista de sistemas, portador do RG nº 2002098456123 SSP/CE, inscrito no CPF nº 294.771.380-45, CNH nº 05543891277, residente na Av. Beira Mar nº 2450, apto. 1402, Meireles, Fortaleza/CE, CEP 60165-121, telefone (+55 85) 99123-4456, e-mail carlos.h.pereira@gmail.com.
O declarante informou que firmou contrato de prestação de serviços tecnológicos com a empresa TECHVISION DESENVOLVIMENTO DIGITAL S.A., inscrita no CNPJ nº 04.812.994/0001-67, com sede na Av. Paulista, nº 1578, 12º andar, Bela Vista, São Paulo/SP, CEP 01310-200, telefone (11) 3456-8800, e-mail institucional contato@techvision.com.br.
O contrato foi registrado sob nº CTR-2023/000918-A, firmado em 02/03/2023, tendo como objeto o desenvolvimento de plataforma digital de gestão documental baseada em Node.js, React e Next.js, pelo valor total de R$ 287.450,90 (duzentos e oitenta e sete mil, quatrocentos e cinquenta reais e noventa centavos).
O pagamento foi pactuado da seguinte forma:

R$ 95.816,96 em 05/03/2023
R$ 95.816,96 em 05/04/2023
R$ 95.816,98 em 05/05/2023
A primeira parcela foi transferida via PIX para a chave financeiro.techvision@gmail.com, vinculada à conta bancária de titularidade de Eduardo Matheus Lacerda, CPF 118.004.770-09, junto ao Banco Itaú Unibanco S.A., agência 8421, conta corrente 0098874-2.
Posteriormente verificou-se que o referido indivíduo também aparece como sócio administrador da empresa LACERDA CONSULTORIA TECNOLÓGICA LTDA, inscrita no CNPJ nº 19.771.205/0001-44, localizada na Rua Vergueiro nº 3057, sala 84, Vila Mariana, São Paulo/SP, CEP 04101-300.
Consta nos autos que o responsável técnico indicado no contrato seria Eng. Ricardo Augusto Nogueira, inscrito no CPF nº 482.117.990-12, CREA nº 152874563-9, residente na Rua Barão de Studart nº 1780, Fortaleza/CE.
Durante diligência preliminar verificou-se que a empresa também possui como sócia a Sra. Juliana Batista Moreira, inscrita no CPF nº 772.551.330-00, RG nº 321455987 SSP/SP, residente na Rua Frei Caneca nº 550, São Paulo/SP, CEP 01307-001.
Em consulta ao sistema da Receita Federal do Brasil, verificou-se capital social declarado no valor de R$ 1.200.000,00.
Também foram anexados aos autos os seguintes documentos:

Nota Fiscal nº 00089452, emitida em 05/03/2023
Nota Fiscal nº 00089453, emitida em 05/04/2023
Protocolo administrativo nº 2023-MPCE-458721
Boletim de Ocorrência nº 2023-00458712
Processo judicial nº 0812345-62.2023.8.06.0001
Consta ainda que o investigado compareceu às reuniões conduzindo o veículo BMW 320i 2021, placa QXT-7H41, RENAVAM nº 01122334455, chassi WBA8E9G50HNU12345.
Durante as tratativas foram utilizados os seguintes contatos adicionais:

telefone comercial (11) 98888-7721
e-mail eduardo.lacerda.dev@protonmail.com
e-mail corporativo financeiro@lacerda-consult.com
Há ainda registro de transferência complementar no valor de R$ 12.450,00, realizada em 11/04/2023, identificador bancário TRX-889127331-ITAU.
Diante dos fatos narrados, vislumbra-se, em tese, possível enquadramento nas seguintes disposições legais:

Art. 171 do Código Penal – Estelionato
Art. 299 do Código Penal – Falsidade ideológica
Art. 288 do Código Penal – Associação criminosa
Art. 186 do Código Civil – Ato ilícito
Art. 927 do Código Civil – Dever de indenizar
Art. 421 do Código Civil – Função social do contrato
Art. 14 do Código de Defesa do Consumidor (Lei nº 8.078/1990)
Art. 129, III da Constituição Federal
Art. 5º, II do Código de Processo Penal
Consta ainda manifestação do advogado Dr. Fernando Castro Albuquerque, inscrito na OAB/CE nº 41.882, com escritório profissional situado na Av. Santos Dumont nº 2789, sala 1105, Fortaleza/CE.
Nada mais havendo, foi lavrado o presente termo.
Fortaleza/CE, 27 de maio de 2023."""

    print("=" * 60)
    print("NER JURÍDICO v2.8 — Teste Definitivo")
    print("=" * 60)

    rel = ner.relatorio(TEXTO_ROBUSTO)

    print(f"\nTotal de entidades : {rel['total_entidades']}")
    print(f"Dados pessoais     : {rel['dados_pessoais']}")
    print(f"Score LGPD         : {rel['score_lgpd']}/100 — risco {rel['risco']}")

    print("\nEntidades encontradas:")
    for tipo, valores in rel["entidades"].items():
        lgpd = " 🔒" if PADROES[tipo]["lgpd"] else ""
        desc = PADROES[tipo]["descricao"]
        print(f"\n  [{tipo}]{lgpd} — {desc}")
        for v in valores:
            print(f"    → {v}")