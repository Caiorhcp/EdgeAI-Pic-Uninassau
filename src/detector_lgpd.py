# src/detector_lgpd.py — v1.0
# Detecta violações da LGPD em documentos jurídicos
# Baseado na Lei 13.709/2018 — artigos 7, 11, 14, 37, 46, 48

import re
from dataclasses import dataclass, field
from typing import List, Dict

# ─── Estrutura de uma violação ────────────────────────────────────────────────
@dataclass
class Violacao:
    tipo:        str
    severidade:  str        # CRÍTICA | ALTA | MÉDIA | BAIXA
    artigo:      str        # artigo da LGPD violado
    descricao:   str        # descrição legível
    evidencia:   str        # trecho do texto que gerou o alerta
    recomendacao: str       # o que fazer para corrigir

# ─── Definição das regras de violação ────────────────────────────────────────
# Cada regra verifica um padrão no texto + condições do relatório NER

REGRAS = [

    # ── Artigo 7 — Base legal para tratamento ─────────────────────────────────
    {
        "id":         "SEM_BASE_LEGAL",
        "tipo":       "Dados pessoais sem base legal aparente",
        "severidade": "CRÍTICA",
        "artigo":     "Art. 7º, LGPD",
        "descricao":  "Dados pessoais (CPF, CNPJ, e-mail, telefone) presentes no documento "
                      "sem menção a base legal que autorize o tratamento.",
        "recomendacao": "Incluir cláusula explicitando a base legal utilizada (ex: "
                        "consentimento do titular, cumprimento de obrigação legal, "
                        "execução de contrato).",
        "verificar": lambda texto, ner, classe: (
            ner["dados_pessoais"] > 0
            and not _menciona_base_legal(texto)
            and classe not in ("lgpd",)
        ),
    },

    # ── Artigo 11 — Dados sensíveis ───────────────────────────────────────────
    {
        "id":         "DADOS_SENSIVEIS_SEM_PROTECAO",
        "tipo":       "Dados sensíveis sem proteção adequada",
        "severidade": "CRÍTICA",
        "artigo":     "Art. 11º, LGPD",
        "descricao":  "Dados de saúde, origem racial, convicção religiosa ou biometria "
                      "detectados sem indicação de medidas de segurança ou consentimento "
                      "específico.",
        "recomendacao": "Dados sensíveis exigem consentimento específico e destacado do "
                        "titular (Art. 11, I) ou uma das hipóteses do Art. 11, II.",
        "verificar": lambda texto, ner, classe: _contem_dados_sensiveis(texto),
    },

    # ── Artigo 14 — Dados de crianças ─────────────────────────────────────────
    {
        "id":         "DADOS_CRIANCAS",
        "tipo":       "Possível tratamento de dados de crianças",
        "severidade": "ALTA",
        "artigo":     "Art. 14º, LGPD",
        "descricao":  "Menção a menores de idade sem indicação de consentimento "
                      "dos pais ou responsáveis.",
        "recomendacao": "O tratamento de dados de crianças e adolescentes deve ser "
                        "realizado com consentimento específico dos pais ou responsável "
                        "legal.",
        "verificar": lambda texto, ner, classe: _menciona_criancas(texto),
    },

    # ── Artigo 37 — Registro de operações ────────────────────────────────────
    {
        "id":         "SEM_REGISTRO_OPERACOES",
        "tipo":       "Transferência de dados sem registro de operações",
        "severidade": "ALTA",
        "artigo":     "Art. 37º, LGPD",
        "descricao":  "Documento menciona compartilhamento ou transferência de dados "
                      "pessoais sem indicação de registro das operações de tratamento.",
        "recomendacao": "Controladores e operadores devem manter registro das operações "
                        "de tratamento (Art. 37). Incluir cláusula de registro e "
                        "indicar encarregado (DPO).",
        "verificar": lambda texto, ner, classe: (
            _menciona_compartilhamento(texto)
            and ner["dados_pessoais"] > 0
            and not _menciona_registro(texto)
        ),
    },

    # ── Artigo 46 — Segurança ─────────────────────────────────────────────────
    {
        "id":         "SEM_MEDIDAS_SEGURANCA",
        "tipo":       "Ausência de medidas de segurança",
        "severidade": "ALTA",
        "artigo":     "Art. 46º, LGPD",
        "descricao":  "Dados pessoais tratados sem menção a medidas técnicas e "
                      "administrativas de segurança para proteção contra acesso "
                      "não autorizado.",
        "recomendacao": "Incluir cláusula de segurança da informação: criptografia, "
                        "controle de acesso, política de senhas e plano de resposta "
                        "a incidentes.",
        "verificar": lambda texto, ner, classe: (
            ner["dados_pessoais"] >= 2
            and not _menciona_seguranca(texto)
            and classe == "contrato"
        ),
    },

    # ── Artigo 48 — Notificação de incidentes ─────────────────────────────────
    {
        "id":         "SEM_NOTIFICACAO_INCIDENTES",
        "tipo":       "Ausência de cláusula de notificação de incidentes",
        "severidade": "MÉDIA",
        "artigo":     "Art. 48º, LGPD",
        "descricao":  "Contrato com tratamento de dados pessoais sem cláusula de "
                      "notificação de incidentes de segurança à ANPD e ao titular.",
        "recomendacao": "Incluir cláusula obrigando notificação em prazo razoável "
                        "(recomendado: 72h) após ciência do incidente, conforme "
                        "orientação da ANPD.",
        "verificar": lambda texto, ner, classe: (
            classe == "contrato"
            and ner["dados_pessoais"] > 0
            and not _menciona_incidentes(texto)
        ),
    },

    # ── Finalidade incompatível ────────────────────────────────────────────────
    {
        "id":         "FINALIDADE_INCOMPATIVEL",
        "tipo":       "Possível uso de dados fora da finalidade declarada",
        "severidade": "ALTA",
        "artigo":     "Art. 6º, I, LGPD",
        "descricao":  "Dados pessoais coletados para uma finalidade mas com cláusulas "
                      "que permitem uso para outras finalidades sem restrição.",
        "recomendacao": "Limitar o uso dos dados à finalidade específica declarada. "
                        "Qualquer uso diverso exige nova base legal ou consentimento.",
        "verificar": lambda texto, ner, classe: _finalidade_aberta(texto),
    },

    # ── Retenção excessiva ─────────────────────────────────────────────────────
    {
        "id":         "RETENCAO_EXCESSIVA",
        "tipo":       "Retenção de dados além do necessário",
        "severidade": "MÉDIA",
        "artigo":     "Art. 15º, LGPD",
        "descricao":  "Cláusula de sigilo ou retenção de dados com prazo superior "
                      "a 10 anos sem justificativa legal específica.",
        "recomendacao": "Definir prazo de retenção compatível com a finalidade. "
                        "Após o término, os dados devem ser eliminados ou anonimizados.",
        "verificar": lambda texto, ner, classe: _retencao_excessiva(texto),
    },

    # ── Transferência internacional ────────────────────────────────────────────
    {
        "id":         "TRANSFERENCIA_INTERNACIONAL",
        "tipo":       "Transferência internacional sem garantias",
        "severidade": "ALTA",
        "artigo":     "Art. 33º, LGPD",
        "descricao":  "Menção a transferência de dados para outro país sem indicação "
                      "de que o país destinatário oferece proteção adequada.",
        "recomendacao": "A transferência internacional só é permitida para países com "
                        "nível adequado de proteção (Art. 33, I) ou mediante cláusulas "
                        "contratuais padrão aprovadas pela ANPD.",
        "verificar": lambda texto, ner, classe: _transferencia_internacional(texto),
    },

    # ── Encarregado (DPO) ─────────────────────────────────────────────────────
    {
        "id":         "SEM_ENCARREGADO",
        "tipo":       "Ausência de indicação do encarregado (DPO)",
        "severidade": "BAIXA",
        "artigo":     "Art. 41º, LGPD",
        "descricao":  "Documento de grande volume de dados pessoais sem indicação "
                      "do encarregado pelo tratamento de dados (Data Protection Officer).",
        "recomendacao": "Indicar o encarregado e seus dados de contato. O encarregado "
                        "atua como canal entre o controlador, os titulares e a ANPD.",
        "verificar": lambda texto, ner, classe: (
            ner["dados_pessoais"] >= 3
            and not _menciona_encarregado(texto)
        ),
    },
]

# ─── Funções auxiliares de análise de texto ──────────────────────────────────

def _menciona_base_legal(texto: str) -> bool:
    """Verifica se o texto menciona alguma base legal do Art. 7 da LGPD."""
    padroes = [
        r"\bconsentimento\b", r"\bobriga[çc][ãa]o\s+legal\b",
        r"\bexecu[çc][ãa]o\s+de\s+contrato\b", r"\bleg[íi]timo\s+interesse\b",
        r"\bprote[çc][ãa]o\s+da\s+vida\b", r"\btutela\s+da\s+sa[úu]de\b",
        r"\binteresse\s+p[úu]blico\b", r"\bexerc[íi]cio\s+de\s+direitos\b",
        r"\bartigo\s+7\b", r"\bart\.?\s*7[º°]?\s*da\s+lgpd\b",
        r"\bbase\s+legal\b", r"\bfundamento\s+legal\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _contem_dados_sensiveis(texto: str) -> bool:
    """Detecta menção a dados pessoais sensíveis (Art. 5, II, LGPD)."""
    padroes = [
        r"\borigem\s+racial\b", r"\brigem\s+[eé]tnica\b",
        r"\bconvi[çc][ãa]o\s+religiosa\b", r"\bopini[ãa]o\s+pol[íi]tica\b",
        r"\bfilia[çc][ãa]o\s+sindical\b", r"\bsaúde\b", r"\bbiom[eé]tric[ao]\b",
        r"\bgen[eé]tic[ao]\b", r"\borienta[çc][ãa]o\s+sexual\b",
        r"\bdiagnóstico\b", r"\bprontuário\b", r"\bexame\s+médico\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _menciona_criancas(texto: str) -> bool:
    padroes = [
        r"\bcrian[çc]a\b", r"\badolescente\b", r"\bmenor\s+de\s+idade\b",
        r"\bmenor\s+de\s+\d+\s+anos\b", r"\brespons[aá]vel\s+legal\b",
        r"\bguarda\b.*\bmenor\b", r"\btutela\b.*\bmenor\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _menciona_compartilhamento(texto: str) -> bool:
    padroes = [
        r"\bcompartilhamento\b", r"\btransfer[eê]ncia\b",
        r"\bceder\b", r"\bcess[ãa]o\b", r"\bdivulgar\b",
        r"\bterceiros\b", r"\bfornecedor\b.*\bdados\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _menciona_registro(texto: str) -> bool:
    padroes = [
        r"\bregistro\s+de\s+opera[çc][õo]es\b",
        r"\bregistro\s+de\s+tratamento\b",
        r"\blog\b.*\bdados\b", r"\bauditoria\b",
        r"\bencarregado\b", r"\bdpo\b",
        r"\bartigo\s+37\b", r"\bart\.?\s*37\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _menciona_seguranca(texto: str) -> bool:
    padroes = [
        r"\bmedidas\s+de\s+seguran[çc]a\b", r"\bcriptograf\b",
        r"\bcontrole\s+de\s+acesso\b", r"\bfirewall\b",
        r"\bseguran[çc]a\s+da\s+informa[çc][ãa]o\b",
        r"\bpolítica\s+de\s+privacidade\b", r"\bprote[çc][ãa]o\s+de\s+dados\b",
        r"\bconfidencialidade\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _menciona_incidentes(texto: str) -> bool:
    padroes = [
        r"\bincidente\b.*\bseguran[çc]a\b", r"\bvazamento\b",
        r"\bnotifica[çc][ãa]o\b.*\banpd\b", r"\bnotifica[çc][ãa]o\b.*\bincidente\b",
        r"\bartigo\s+48\b", r"\bbrecha\b.*\bseguran[çc]a\b",
        r"\bresposta\b.*\bincidente\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _finalidade_aberta(texto: str) -> bool:
    """Detecta cláusulas que permitem uso irrestrito dos dados."""
    padroes = [
        r"\bqualquer\s+finalidade\b",
        r"\bqualquer\s+uso\b",
        r"\buso\s+irrestrito\b",
        r"\ba\s+crit[eé]rio\s+(?:exclusivo\s+)?d[ao]\b.*\bdados\b",
        r"\busar\s+os\s+dados\s+para\s+(?:quaisquer|qualquer)\b",
        r"\bfinalidades\s+diversas\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _retencao_excessiva(texto: str) -> bool:
    """Detecta prazos de retenção ou sigilo superiores a 10 anos."""
    t = texto.lower()
    # Procura padrões como "por 15 anos", "20 anos após", "prazo indeterminado"
    matches = re.findall(
        r"\b(\d+)\s*anos?\b.*?\b(?:sigilo|reten[çc][ãa]o|guardar|manter|armazenar)\b"
        r"|\b(?:sigilo|reten[çc][ãa]o|guardar|manter|armazenar)\b.*?\b(\d+)\s*anos?\b",
        t
    )
    for m in matches:
        anos = int(m[0] or m[1] or 0)
        if anos > 10:
            return True
    if re.search(r"\bprazo\s+indeterminado\b|\bperpetua(?:mente|l)?\b", t):
        return True
    return False

def _transferencia_internacional(texto: str) -> bool:
    padroes = [
        r"\btransfer[eê]ncia\s+internacional\b",
        r"\bexterior\b.*\bdados\b",
        r"\bdados\b.*\bexterior\b",
        r"\bservidor\b.*\b(?:eua|usa|europa|aws|azure|google\s+cloud)\b",
        r"\bnuvem\s+(?:internacional|global|externa)\b",
        r"\bhosting\b.*\bfora\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

def _menciona_encarregado(texto: str) -> bool:
    padroes = [
        r"\bencarregado\b", r"\bdpo\b",
        r"\bdata\s+protection\s+officer\b",
        r"\brespons[aá]vel\s+pelo\s+tratamento\b",
        r"\bartigo\s+41\b", r"\bart\.?\s*41\b",
    ]
    t = texto.lower()
    return any(re.search(p, t) for p in padroes)

# ─── Detector principal ───────────────────────────────────────────────────────
class DetectorLGPD:

    def analisar(self, texto: str, relatorio_ner: dict, classe: str) -> dict:
        """
        Analisa o documento e retorna todas as violações detectadas.

        Args:
            texto:         texto completo do documento
            relatorio_ner: saída do NERJuridico.relatorio()
            classe:        classe detectada pelo modelo (lgpd, contrato, etc.)

        Returns:
            dict com violações, score de conformidade e recomendações
        """
        violacoes = []

        for regra in REGRAS:
            try:
                if regra["verificar"](texto, relatorio_ner, classe):
                    # Busca evidência: trecho relevante do texto
                    evidencia = _extrair_evidencia(texto, regra["id"])
                    violacoes.append(Violacao(
                        tipo=regra["tipo"],
                        severidade=regra["severidade"],
                        artigo=regra["artigo"],
                        descricao=regra["descricao"],
                        evidencia=evidencia,
                        recomendacao=regra["recomendacao"],
                    ))
            except Exception:
                continue

        # Score de conformidade (0–100)
        # Começa em 100 e desconta por violação conforme severidade
        penalidades = {"CRÍTICA": 30, "ALTA": 20, "MÉDIA": 10, "BAIXO": 5}
        score = 100
        for v in violacoes:
            score -= penalidades.get(v.severidade, 5)
        score = max(0, score)

        nivel = (
            "NÃO CONFORME"       if score < 40
            else "ATENÇÃO"       if score < 70
            else "PARCIALMENTE CONFORME" if score < 90
            else "CONFORME"
        )

        return {
            "violacoes":        violacoes,
            "total":            len(violacoes),
            "criticas":         sum(1 for v in violacoes if v.severidade == "CRÍTICA"),
            "altas":            sum(1 for v in violacoes if v.severidade == "ALTA"),
            "medias":           sum(1 for v in violacoes if v.severidade == "MÉDIA"),
            "baixas":           sum(1 for v in violacoes if v.severidade == "BAIXA"),
            "score_conformidade": score,
            "nivel":            nivel,
        }

def _extrair_evidencia(texto: str, regra_id: str) -> str:
    """Extrai um trecho relevante do texto como evidência da violação."""
    mapa = {
        "SEM_BASE_LEGAL":            r"\bdados\s+pessoais\b|\bcpf\b|\bcnpj\b",
        "DADOS_SENSIVEIS_SEM_PROTECAO": r"\bsaúde\b|\bbiométric\b|\bgenétic\b",
        "DADOS_CRIANCAS":            r"\bcrian[çc]a\b|\badolescente\b|\bmenor\b",
        "SEM_REGISTRO_OPERACOES":    r"\bcompartilhamento\b|\btransfer[eê]ncia\b",
        "SEM_MEDIDAS_SEGURANCA":     r"\bdados\s+pessoais\b",
        "SEM_NOTIFICACAO_INCIDENTES":r"\bdados\s+pessoais\b|\bincidente\b",
        "FINALIDADE_INCOMPATIVEL":   r"\bqualquer\s+finalidade\b|\buso\s+irrestrito\b",
        "RETENCAO_EXCESSIVA":        r"\b\d+\s*anos?\b",
        "TRANSFERENCIA_INTERNACIONAL":r"\bexterior\b|\bnuvem\b|\binternacional\b",
        "SEM_ENCARREGADO":           r"\bdados\s+pessoais\b|\bcontrolador\b",
    }
    padrao = mapa.get(regra_id, r"\bdados\b")
    m = re.search(padrao, texto, re.IGNORECASE)
    if m:
        inicio = max(0, m.start() - 60)
        fim    = min(len(texto), m.end() + 80)
        trecho = texto[inicio:fim].strip()
        trecho = re.sub(r"\s+", " ", trecho)
        return f"…{trecho}…"
    return "—"


# ─── Teste standalone ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    from src.ner_juridico import NERJuridico

    detector = DetectorLGPD()
    ner      = NERJuridico()

    TEXTOS = [
        {
            "titulo": "Contrato problemático (muitas violações)",
            "classe": "contrato",
            "texto": """
            Contrato de Prestação de Serviços. A contratada ACME LTDA,
            CNPJ 12.345.678/0001-99, coletará dados pessoais do contratante
            João Silva, CPF 123.456.789-09, telefone (11) 99999-9999,
            e-mail joao@email.com, para qualquer finalidade que julgar
            conveniente. Os dados serão mantidos por 20 anos após o término
            do contrato. Os dados poderão ser transferidos para servidores
            nos EUA sem restrições. Inclui dados de saúde do paciente.
            """,
        },
        {
            "titulo": "Contrato conforme com LGPD",
            "classe": "contrato",
            "texto": """
            Contrato de Prestação de Serviços. A contratada coletará dados
            pessoais com base legal no consentimento do titular (Art. 7, I, LGPD)
            exclusivamente para execução deste contrato. Medidas de segurança:
            criptografia AES-256, controle de acesso e política de senhas.
            O encarregado pelo tratamento é João Pereira, dpo@empresa.com.
            Em caso de incidente de segurança, a ANPD será notificada em 72h.
            Os dados serão eliminados em 5 anos após o término do contrato.
            Registro de operações mantido conforme artigo 37 da LGPD.
            """,
        },
    ]

    SEV_COR = {
        "CRÍTICA": "🔴",
        "ALTA":    "🟠",
        "MÉDIA":   "🟡",
        "BAIXA":   "🟢",
    }

    for item in TEXTOS:
        rel_ner = ner.relatorio(item["texto"])
        result  = detector.analisar(item["texto"], rel_ner, item["classe"])

        print(f"\n{'='*60}")
        print(f"📄 {item['titulo']}")
        print(f"{'='*60}")
        print(f"Score de conformidade: {result['score_conformidade']}/100 — {result['nivel']}")
        print(f"Violações: {result['total']} "
              f"({result['criticas']} críticas, {result['altas']} altas, "
              f"{result['medias']} médias, {result['baixas']} baixas)")

        if result["violacoes"]:
            print("\nViolações detectadas:")
            for v in result["violacoes"]:
                print(f"\n  {SEV_COR[v.severidade]} [{v.severidade}] {v.tipo}")
                print(f"     Artigo    : {v.artigo}")
                print(f"     Descrição : {v.descricao[:80]}…")
                print(f"     Evidência : {v.evidencia[:80]}")
                print(f"     Correção  : {v.recomendacao[:80]}…")
        else:
            print("\n  ✅ Nenhuma violação detectada.")