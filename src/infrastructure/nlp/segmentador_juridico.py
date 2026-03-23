# src/infrastructure/nlp/segmentador_juridico.py
# Adaptador de infraestrutura — Segmentação de Textos Jurídicos em Blocos

import re
import spacy
from typing import List
from typing_extensions import TypedDict
from src.shared.logger import get_logger

logger = get_logger(__name__)

try:
    nlp = spacy.load("pt_core_news_sm", disable=["ner", "tagger", "lemmatizer"])
except OSError:
    nlp = None


class BlocoJuridico(TypedDict):
    """Representa uma unidade lógica de texto jurídico."""
    tipo: str       # 'Preâmbulo', 'Cláusula X', 'Artigo Y', 'Parágrafo Z', 'Genérico'
    texto: str
    inicio: int     # Índice do char inicial no texto original
    fim: int        # Índice do char final no texto original


class SegmentadorJuridico:
    """
    Divide um documento em blocos lógicos estruturais em vez de uma string linear.
    Ajuda a cruzar contextos: se um `Dado Sensível` e um `Consentimento`
    aparecem no mesmo "BlocoJuridico", o risco é mitigado.
    """

    def segmentar(self, texto: str) -> List[BlocoJuridico]:
        """
        Divide o texto usando divisores legais comuns (Cláusula, Artigo, Parágrafo).
        Se não houver estrutura clara, quebra por quebras de linha/parágrafos naturais.
        """
        blocos: List[BlocoJuridico] = []
        if not texto.strip():
            return blocos

        # Padrões que iniciam uma nova sessão lógica
        regex_divisor = re.compile(
            r"(?P<tipo>"
            r"\bCl[aá]usula\s+(?:[D|d][eé]cima\s+)?(?:[P|p]rimeira|[S|s]egunda|[T|t]erceira|[Q|q]uarta|[Q|q]uinta|[S|s]exta|[S|s][eé]tima|[O|o]itava|[N|n]ona|[D|d][eé]cima|[V|v]ig[eé]sima|[0-9]+[aAº°]?)\b"
            r"|"
            r"^(?:[Aa]rtigo|[Aa]rt\.)\s*[0-9]+[º°]?"
            r"|"
            r"^(?:§|Par[aá]grafo)\s*(?:[Úú]nico|[0-9]+[º°]?)(?:\.+)?"
            r"|"
            r"^[0-9]+[º°]?\s*-"
            r")\s*",
            flags=re.IGNORECASE | re.MULTILINE
        )

        matches = list(regex_divisor.finditer(texto))

        if not matches:
            # Documento sem estrutura forte: cai no fallback por parágrafos longos 
            # (duplo Enter ou similar)
            return self._segmentar_fallback(texto)

        # O texto antes da primeira marcação é o "Preâmbulo"
        if matches[0].start() > 0:
            preambulo_texto = texto[0:matches[0].start()].strip()
            if preambulo_texto:
                blocos.append(BlocoJuridico(
                    tipo="Preâmbulo",
                    texto=preambulo_texto,
                    inicio=0,
                    fim=matches[0].start()
                ))

        # Iterar sobre as marcações e extrair o conteúdo
        for i, match in enumerate(matches):
            tipo_raw = match.group("tipo").strip().title()
            # Limpar formatações comuns para gerar um tipo limpo (Ex: "Cláusula Primeira", "Art. 1º")
            tipo_limpo = re.sub(r"\s+", " ", tipo_raw)

            inicio_bloco = match.start()
            fim_bloco = matches[i + 1].start() if i + 1 < len(matches) else len(texto)

            texto_bloco = texto[inicio_bloco:fim_bloco].strip()

            if texto_bloco:
                blocos.append(BlocoJuridico(
                    tipo=tipo_limpo,
                    texto=texto_bloco,
                    inicio=inicio_bloco,
                    fim=inicio_bloco + len(texto_bloco)
                ))

        logger.info("Texto segmentado em %d blocos lógicos", len(blocos))
        return blocos

    def _segmentar_fallback(self, texto: str) -> List[BlocoJuridico]:
        """Caso o documento não tenha 'Cláusula' ou 'Artigo', divide por frases (spaCy) ou parágrafo."""
        blocos: List[BlocoJuridico] = []
        
        if nlp is not None and len(texto) < 100000:
            doc = nlp(texto)
            for i, sent in enumerate(doc.sents):
                txt = sent.text.strip()
                if len(txt) > 10:
                    blocos.append(BlocoJuridico(
                        tipo=f"Sentença {i+1}",
                        texto=txt,
                        inicio=sent.start_char,
                        fim=sent.end_char
                    ))
            if blocos: return blocos

        # Fallback do fallback: RegEx de parágrafos
        paragrafos = re.finditer(r"([^\n]+(?:\n[^\n]+)*)", texto)
        
        idx = 1
        for m in paragrafos:
            p_texto = m.group(1).strip()
            if len(p_texto) > 10:
                blocos.append(BlocoJuridico(
                    tipo=f"Parágrafo {idx}",
                    texto=p_texto,
                    inicio=m.start(),
                    fim=m.end()
                ))
                idx += 1
                
        # Se for UM grande bloco sem enter, gerar bloco único
        if not blocos:
            blocos.append(BlocoJuridico(
                tipo="Genérico",
                texto=texto.strip(),
                inicio=0,
                fim=len(texto)
            ))

        return blocos
