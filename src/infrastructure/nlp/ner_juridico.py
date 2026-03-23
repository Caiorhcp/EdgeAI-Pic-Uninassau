# src/infrastructure/nlp/ner_juridico.py — v2.9 (DDD + CPF/CNPJ validados)
# Adaptador de infraestrutura — implementa extração de entidades NER

import re
import spacy
from typing import Callable, Dict, List, Optional
from typing_extensions import TypedDict

from src.domain.entities.entidade_ner import EntidadeNER
from src.shared.logger import get_logger

logger = get_logger(__name__)


class PadraoDef(TypedDict):
    """Tipagem estruturada para cada entrada do dicionário PADROES."""
    regex:    str
    lgpd:     bool
    descricao: str
    validar:  Optional[Callable[[str], bool]]


# ─── Funções de Validação Matemática ─────────────────────────────────────────

def _apenas_digitos(v: str) -> str:
    return re.sub(r"\D", "", v)


def _validar_cpf(valor: str) -> bool:
    """Valida CPF pelos dígitos verificadores (módulo 11)."""
    d = _apenas_digitos(valor)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    # Primeiro dígito verificador: pesos 10..2
    s1 = sum(int(d[j]) * (10 - j) for j in range(9))
    r1 = (s1 * 10 % 11) % 10
    if int(d[9]) != r1:
        return False
    # Segundo dígito verificador: pesos 11..2
    s2 = sum(int(d[j]) * (11 - j) for j in range(10))
    r2 = (s2 * 10 % 11) % 10
    if int(d[10]) != r2:
        return False
    return True


def _validar_cnpj(valor: str) -> bool:
    """Valida CNPJ pelos dígitos verificadores (módulo 11)."""
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


# ─── Padrões de Busca ─────────────────────────────────────────────────────────
# FIX: _validar_cpf e _validar_cnpj agora estão ativados (eram None antes)

PADROES: Dict[str, PadraoDef] = {
    "CNH": {
        "regex":    r"\b(?:CNH|Registro)\s*(?::|n[º°.]?)?\s*\d{11}\b",
        "lgpd":     True,
        "descricao": "Carteira Nacional de Habilitação",
        "validar":  None,
    },
    "RENAVAM": {
        "regex":    r"\bRENAVAM\s*(?::|n[º°.]?)?\s*\d{11}\b",
        "lgpd":     False,
        "descricao": "Registro Nacional de Veículos Automotores",
        "validar":  None,
    },
    "PIS": {
        "regex":    r"\b(?:PIS|NIS|PASEP)\s*(?::|n[º°.]?)?\s*\d{11}\b",
        "lgpd":     True,
        "descricao": "PIS / NIS / PASEP",
        "validar":  None,
    },
    # ── FIX: validação matemática agora ativa ─────────────────────────────────
    "CPF": {
        "regex":    r"\b\d{3}[\.\ ]?\d{3}[\.\ ]?\d{3}[-\.\ ]?\d{2}\b|\b\d{11}\b",
        "lgpd":     True,
        "descricao": "Cadastro de Pessoa Física",
        "validar":  _validar_cpf,       # ← antes era None
    },
    "CNPJ": {
        "regex":    r"\b\d{2}[\.\ ]?\d{3}[\.\ ]?\d{3}[\/\.\ ]?\d{4}[-\.\ ]?\d{2}\b",
        "lgpd":     True,
        "descricao": "Cadastro Nacional de Pessoa Jurídica",
        "validar":  _validar_cnpj,      # ← antes era None
    },
    "RG": {
        "regex":    r"\bRG\s*(?:n[º°.]?\s*)?[\d\.-]+\b",
        "lgpd":     True,
        "descricao": "Registro Geral (Identidade)",
        "validar":  None,
    },
    "EMAIL": {
        "regex":    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "lgpd":     True,
        "descricao": "Endereço de e-mail",
        "validar":  None,
    },
    "TELEFONE": {
        "regex":    r"(?:\(\+?55\s*\d{2}\)\s*|\+?55\s*\d{2}\s*|\(\d{2}\)\s+)(?:9\s*)?\d{4,5}[-\s]?\d{4}\b|\b(?:9\s*)?\d{4,5}-\d{4}\b",
        "lgpd":     True,
        "descricao": "Número de telefone",
        "validar":  None,
    },
    "ENDERECO": {
        "regex":    r"\b(?:Rua|Av\.?|Avenida|Tv\.?|Travessa|Alameda|Al\.?|Rod(?:ovia)?|Praça|Pça\.?)\s+(?:.{2,150}?CEP:?\s*\d{5}[-\s]?\d{3}\b|(?:(?!\b(?:telefone|tel|e-mail|email|CPF|CNPJ|RG|inscrito|portador)\b|\.\s+[A-ZÀ-Ú]|\n).){5,120})",
        "lgpd":     True,
        "descricao": "Endereço Completo",
        "validar":  None,
    },
    "PLACA_VEICULO": {
        "regex":    r"\b(?!CTR-)[A-Z]{3}[-\s]?\d[A-Z0-9]\d{2}\b|\b(?!CTR-)[A-Z]{3}[-\s]?\d{4}\b",
        "lgpd":     False,
        "descricao": "Placa de veículo (Mercosul ou antiga)",
        "validar":  None,
    },
    "OAB": {
        "regex":    r"\bOAB[\/\-\s]?[A-Z]{2}\s*n?[oº°.]?\s*[\d\.]+\b",
        "lgpd":     False,
        "descricao": "Registro OAB",
        "validar":  None,
    },
    "CRM": {
        "regex":    r"\bCRM[\/\-\s]?[A-Z]{2}\s*n?[oº°.]?\s*[\d\.]+\b",
        "lgpd":     False,
        "descricao": "Registro CRM (médico)",
        "validar":  None,
    },
    "PROCESSO_CNJ": {
        "regex":    r"\b\d{7}[-\.]?\d{2}[\.]\d{4}[\.](\d{1})[\.](\d{2})[\.](\d{4})\b",
        "lgpd":     False,
        "descricao": "Número de processo judicial (CNJ)",
        "validar":  None,
    },
    "PROCESSO_ANTIGO": {
        "regex":    r"(?:(?:Proc(?:esso)?|Autos?|Feito)\s*n?[oº°.]?\s*)\d{4,6}[\/\-]\d{2,4}(?:\s*-\s*[A-Z]{2,})?",
        "lgpd":     False,
        "descricao": "Número de processo (formato antigo)",
        "validar":  None,
    },
    "DATA": {
        "regex":    (
            r"\b(?:0?[1-9]|[12]\d|3[01])[\/\-](?:0?[1-9]|1[0-2])[\/\-]\d{2,4}\b"
            r"|\b\d{1,2}\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|"
            r"julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}\b"
        ),
        "lgpd":     False,
        "descricao": "Data",
        "validar":  None,
    },
    "VALOR_MONETARIO": {
        "regex":    r"R\$\s*[\d\.]+(?:,\d{2})?|\b[\d\.]+,\d{2}\s*(?:reais|mil reais)\b",
        "lgpd":     False,
        "descricao": "Valor monetário",
        "validar":  None,
    },
    "PRAZO": {
        "regex":    r"\b\d+\s*(?:\([^)]+\))?\s*(?:dias?\s*úteis?|dias?\s*corridos?|dias?|meses?|anos?|horas?|semanas?)\b",
        "lgpd":     False,
        "descricao": "Prazo",
        "validar":  None,
    },
    "LEI": {
        "regex":    r"\b(?:Lei|LC|Decreto(?:-[Ll]ei)?)\s+(?:Complementar\s+)?(?:n[oº°.]?\s*)?[\d\.]+[\/\.]\d{2,5}(?:\/\d{2,4})?\b",
        "lgpd":     False,
        "descricao": "Lei ou norma",
        "validar":  None,
    },
    "ARTIGO_LEI": {
        "regex":    r"\bart(?:igo)?\.?\s*\d+[º°]?(?:[,\s]+(?:inciso|§|parágrafo|alínea)(?:\s+[IVXivx\d]+[º°]?)?)?\b(?!\s*(?:da\s+)?[Ll]ei)",
        "lgpd":     False,
        "descricao": "Referência a artigo de lei",
        "validar":  None,
    },
    "TRIBUNAL": {
        "regex":    r"\b(?:STF|STJ|TST|TSE|STM|TRF\s*\d?|TRT\s*\d+|TJ[A-Z]{2}|CNJ|CARF|TJSP|TJRJ|TJMG|TJRS|TJPR|TJBA)\b",
        "lgpd":     False,
        "descricao": "Tribunal",
        "validar":  None,
    },
    "SUMULA": {
        "regex":    r"\bS[úu]mula\s+(?:Vinculante\s+)?n?[oº°.]?\s*\d+\b",
        "lgpd":     False,
        "descricao": "Súmula",
        "validar":  None,
    },
    "RECURSO": {
        "regex":    r"\b(?:REsp|AgRg|HC|RHC|MS|RMS|ADI|ADPF|ADC|RE|AI|ARE|ACO|Rcl)\s*n?[oº°.]?\s*[\d\.]+\b",
        "lgpd":     False,
        "descricao": "Número de recurso/ação",
        "validar":  None,
    },
    "CEP": {
        "regex":    r"\bCEP:?\s*\d{5}[-\s]?\d{3}\b",
        "lgpd":     False,
        "descricao": "CEP",
        "validar":  None,
    },
    # ── Evidências Contextuais LGPD (Atenuantes/Garantias) ──
    "CONSENTIMENTO": {
        "regex":    r"\b(?:consentimento|autoriza[çc][ãa]o)\s+(?:express[ao]|expl[íi]cit[ao]|espec[íi]fic[ao]|inequ[íi]voc[ao]|livre)\b",
        "lgpd":     False,
        "descricao": "Consentimento Explicito do Titular",
        "validar":  None,
    },
    "MEDIDA_SEGURANCA": {
        "regex":    r"\b(?:criptograf(?:ia|ado)|anonimiza[çc][ãa]o|pseudoanonimiza[çc][ãa]o|firewall|controle\s+de\s+acesso|seguran[çc]a\s+da\s+informa[çc][ãa]o)\b",
        "lgpd":     False,
        "descricao": "Medida de Segurança Tecnológica",
        "validar":  None,
    },
    "BASE_LEGAL": {
        "regex":    r"\b(?:leg[íi]timo\s+interesse|execu[çc][ãa]o\s+de\s+contrato|obriga[çc][ãa]o\s+legal|exerc[íi]cio\s+regular\s+de\s+direito)\b",
        "lgpd":     False,
        "descricao": "Base Legal explícita",
        "validar":  None,
    },
}

# ─── Inicialização Opcional do spaCy ──────────────────────────────────────────
try:
    nlp = spacy.load("pt_core_news_sm", disable=["parser"])
except OSError:
    logger.warning("Modelo spaCy 'pt_core_news_sm' não encontrado, usando fallback (apenas regex).")
    nlp = None

# ─── Prioridade para resolver sobreposições ───────────────────────────────────
PRIORIDADE = {
    "ENDERECO": 15, "PROCESSO_CNJ": 15,
    "CNH": 12, "RENAVAM": 12, "PIS": 12,
    "CEP": 10, "CPF": 8, "CNPJ": 8, "RG": 8, "EMAIL": 8,
    "TELEFONE": 7, "LEI": 7,
    "DATA": 6,
    "PLACA_VEICULO": 5,
    "OAB": 4, "CRM": 4, "ARTIGO_LEI": 4, "RECURSO": 4,
    "PROCESSO_ANTIGO": 3,
    "VALOR_MONETARIO": 2, "PRAZO": 2,
    "ORG": 1, "PER": 1, "LOC": 1, "MISC": 1,
    "TRIBUNAL": 1, "SUMULA": 1,
    "CONSENTIMENTO": 20, "MEDIDA_SEGURANCA": 20, "BASE_LEGAL": 20,
}


# ─── Adaptador de Infraestrutura ─────────────────────────────────────────────

class NERJuridico:
    """
    Adaptador de infraestrutura para extração de entidades jurídicas.
    Usa regex especializado + validação matemática de CPF/CNPJ.
    """

    def _normalizar_ocr(self, texto: str) -> str:
        """Corrige erros comuns de OCR em números (O→0, l→1)."""
        texto = re.sub(r"(?<=\d)O(?=\d)", "0", texto)
        texto = re.sub(r"(?<=\d)o(?=\d)", "0", texto)
        texto = re.sub(r"(?<=\d)l(?=\d)", "1", texto)
        return texto

    def _resolver_sobreposicoes(self, entidades: List[EntidadeNER]) -> List[EntidadeNER]:
        """Remove entidades sobrepostas mantendo a de maior prioridade."""
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
                p_novo     = PRIORIDADE.get(e.tipo, 0)
                p_anterior = PRIORIDADE.get(resultado[-1].tipo, 0)
                if p_novo > p_anterior:
                    resultado[-1] = e
                    ultimo_fim = e.fim

        return resultado

    @staticmethod
    def _validar_valor(valor: str, validar_fn: Optional[Callable[[str], bool]]) -> bool:
        """Aplica a função de validação específica do padrão, se existir."""
        if validar_fn is None:
            return True
        return validar_fn(valor)

    def extrair(self, texto: str) -> List[EntidadeNER]:
        """Extrai todas as entidades jurídicas do texto."""
        texto_norm = self._normalizar_ocr(texto).replace('\n', ' ')

        todas: List[EntidadeNER] = []
        for tipo, cfg in PADROES.items():
            padrao: str = cfg["regex"]
            validar_fn: Optional[Callable[[str], bool]] = cfg["validar"]
            for m in re.finditer(padrao, texto_norm, re.IGNORECASE | re.UNICODE):
                valor = m.group().strip(" ,.;")
                if not self._validar_valor(valor, validar_fn):
                    continue
                todas.append(EntidadeNER(
                    tipo=tipo,
                    valor=valor,
                    inicio=m.start(),
                    fim=m.end(),
                    risco_lgpd=cfg["lgpd"],
                ))

        # --- spaCy NER Organico ---
        if nlp is not None:
            doc = nlp(texto_norm)
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PER", "LOC", "MISC"]:
                    todas.append(EntidadeNER(
                        tipo=ent.label_,
                        valor=ent.text.strip(" ,.;"),
                        inicio=ent.start_char,
                        fim=ent.end_char,
                        risco_lgpd=(ent.label_ == "PER"),
                    ))

        todas = sorted(todas, key=lambda e: e.inicio)
        todas = self._resolver_sobreposicoes(todas)

        # Deduplicar por valor normalizado
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
        """Gera relatório estruturado com entidades e score LGPD."""
        entidades = self.extrair(texto)

        agrupado: Dict[str, List[str]] = {}
        for e in entidades:
            agrupado.setdefault(e.tipo, [])
            if e.valor not in agrupado[e.tipo]:
                agrupado[e.tipo].append(e.valor)

        dados_pessoais = [e for e in entidades if e.risco_lgpd]

        pesos = {
            "CPF": 30, "CNPJ": 20, "RG": 20, "CNH": 20, "PIS": 15,
            "EMAIL": 20, "TELEFONE": 15, "ENDERECO": 10, "PLACA_VEICULO": 5,
        }
        score = sum(pesos[t] for t in pesos if t in {e.tipo for e in dados_pessoais})
        score = min(score, 100)

        return {
            "total_entidades": len(entidades),
            "dados_pessoais":  len(dados_pessoais),
            "score_lgpd":      score,
            "risco":           "ALTO" if score >= 50 else "MÉDIO" if score >= 20 else "BAIXO",
            "entidades":       agrupado,
            "entidades_raw":   entidades,
        }
