# src/domain/services/lgpd_service.py
# Serviço de domínio: análise de conformidade com a LGPD usando Binding de Contexto

import re
from typing import List, Dict, Any
from thefuzz import fuzz

from src.domain.entities.violacao_lgpd import ViolacaoLGPD
from src.domain.value_objects.severidade import Severidade
from src.shared.logger import get_logger

logger = get_logger(__name__)


class LGPDService:
    """
    Serviço de domínio para análise de conformidade com a LGPD.
    Usa um motor de Regras em Blocos (Context Binding) com pesos de evidências.
    """

    def analisar(self, blocos_analisados: List[Dict[str, Any]], classe: str) -> Dict[str, Any]:
        """
        Analisa o documento processando bloco a bloco.
        Se um bloco tem dado sensível mas também tem Consentimento/Segurança, 
        o risco é mitigado internamente pelo "Context Binding".
        
        Args:
            blocos_analisados: Lista de dicts {"bloco": BlocoJuridico, "ner": relatorio_ner_bloco}
            classe: A classe do documento detectada.
        """
        violacoes: List[ViolacaoLGPD] = []
        blocos_detalhados = []
        score_geral = 100

        for b_data in blocos_analisados:
            bloco = b_data["bloco"]
            ner = b_data["ner"]
            texto = bloco["texto"]
            tipo_bloco = bloco["tipo"]
            
            entidades_tipos = list(ner["entidades"].keys())
            qtd_dados_pessoais = ner["dados_pessoais"]
            
            # --- Checagem de Evidências no Bloco (Context Binding) ---
            t = texto.lower()
            tem_dado_sensivel = "dados sensíveis" in t or any(
                pt in t for pt in ["saúde", "biometria", "racial", "religião", "orientação sexual"]
            )
            tem_crianca = "criança" in t or "menor de idade" in t or "adolescente" in t or fuzz.partial_ratio("menor de idade", t) > 88
            tem_transferencia = "transferência internacional" in t or "exterior" in t or "nuvem global" in t or fuzz.partial_ratio("transferencia internacional", t) > 88

            tem_consentimento = "CONSENTIMENTO" in entidades_tipos or fuzz.partial_ratio("consentimento expresso", t) > 85 or fuzz.partial_ratio("consentimento explicito", t) > 85
            tem_seguranca = "MEDIDA_SEGURANCA" in entidades_tipos or fuzz.partial_ratio("medidas de seguranca", t) > 88 or fuzz.partial_ratio("criptografia", t) > 88
            tem_base_legal = "BASE_LEGAL" in entidades_tipos or fuzz.partial_ratio("legitimo interesse", t) > 88 or fuzz.partial_ratio("obrigacao legal", t) > 88
            
            # Avaliação de Risco do Bloco
            score_bloco = 100
            violacoes_bloco = []

            # Regra 1: Dados Sensíveis sem Proteção
            if tem_dado_sensivel:
                if tem_consentimento or tem_base_legal:
                    score_bloco -= 10 # Risco mitigado
                    v = ViolacaoLGPD(
                        tipo="Dados sensíveis processados com mitigação",
                        severidade=Severidade.BAIXA,
                        artigo="Art. 11º, LGPD",
                        descricao="Dados sensíveis identificados, mas base legal ou consentimento está presente no mesmo contexto.",
                        evidencia=f"[{tipo_bloco}] {texto[:60]}...",
                        recomendacao="Revisar se o consentimento é válido e inequívoco."
                    )
                    violacoes_bloco.append(v)
                else:
                    score_bloco -= Severidade.CRITICA.penalidade
                    v = ViolacaoLGPD(
                        tipo="Dados sensíveis sem base legal explícita no bloco",
                        severidade=Severidade.CRITICA,
                        artigo="Art. 11º, LGPD",
                        descricao="Dados sensíveis identificados sem consentimento ou base legal explícita no mesmo contexto.",
                        evidencia=f"[{tipo_bloco}] {texto[:60]}...",
                        recomendacao="Adicionar consentimento destacado (Art 11, I) no mesmo contexto."
                    )
                    violacoes_bloco.append(v)

            # Regra 2: Dados de Crianças
            if tem_crianca:
                if not tem_consentimento:
                    score_bloco -= Severidade.ALTA.penalidade
                    v = ViolacaoLGPD(
                        tipo="Dados de menores sem consentimento dos pais",
                        severidade=Severidade.ALTA,
                        artigo="Art. 14º, LGPD",
                        descricao="Menção a crianças sem indicação de consentimento explícito no bloco.",
                        evidencia=f"[{tipo_bloco}] {texto[:60]}...",
                        recomendacao="Incluir consentimento específico de um dos pais (Art. 14, §1º)."
                    )
                    violacoes_bloco.append(v)

            # Regra 3: Falta de Medidas de Segurança para Dados Pessoais
            if qtd_dados_pessoais > 0 and classe == "contrato":
                if not tem_seguranca:
                    v = ViolacaoLGPD(
                        tipo="Tratamento sem menção a segurança no contexto",
                        severidade=Severidade.MEDIA,
                        artigo="Art. 46º, LGPD",
                        descricao="Dados pessoais tratados sem explicitá-los junto a medidas de proteção (criptografia, firewalls).",
                        evidencia=f"[{tipo_bloco}] {texto[:60]}...",
                        recomendacao="Adicionar cláusula/referência de medidas de segurança."
                    )
                    violacoes_bloco.append(v)
                    score_bloco -= Severidade.MEDIA.penalidade
                    
            # Regra 4: Transferência Internacional sem salvaguarda
            if tem_transferencia:
                if not tem_seguranca and not tem_base_legal:
                    score_bloco -= Severidade.ALTA.penalidade
                    v = ViolacaoLGPD(
                        tipo="Transferência internacional sem garantias",
                        severidade=Severidade.ALTA,
                        artigo="Art. 33º, LGPD",
                        descricao="Transferência para o exterior sem mitigação explícita de segurança ou base.",
                        evidencia=f"[{tipo_bloco}] {texto[:60]}...",
                        recomendacao="Indicar salvaguardas (cláusula contratual padrão, anonimização)."
                    )
                    violacoes_bloco.append(v)

            # Atualizar globais
            if violacoes_bloco:
                blocos_detalhados.append({
                    "tipo": tipo_bloco,
                    "score": max(0, score_bloco),
                    "violacoes": violacoes_bloco,
                })
                violacoes.extend(violacoes_bloco)
                score_geral -= (100 - max(0, score_bloco)) # Propaga o impacto

        score_geral = max(0, score_geral)
        nivel = (
            "NÃO CONFORME"          if score_geral < 40
            else "ATENÇÃO"          if score_geral < 70
            else "PARCIALMENTE CONFORME" if score_geral < 90
            else "CONFORME"
        )

        return {
            "violacoes":          violacoes,
            "blocos_detalhados":  blocos_detalhados,
            "total":              len(violacoes),
            "criticas":           sum(1 for v in violacoes if v.severidade == Severidade.CRITICA),
            "altas":              sum(1 for v in violacoes if v.severidade == Severidade.ALTA),
            "medias":             sum(1 for v in violacoes if v.severidade == Severidade.MEDIA),
            "baixas":             sum(1 for v in violacoes if v.severidade == Severidade.BAIXA),
            "score_conformidade": score_geral,
            "nivel":              nivel,
        }
