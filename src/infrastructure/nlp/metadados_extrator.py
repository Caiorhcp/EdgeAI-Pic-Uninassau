# src/infrastructure/nlp/metadados_extrator.py
# Componente de Infraestrutura — Raspagem e extração refinada de metadados de arquivos de processos.

import re
from typing import Dict, Any, List

class MetadadosExtrator:
    """
    Motor local robusto para raspar e extrair metadados estruturados
    a partir do texto integral de qualquer processo judicial.
    """

    def __init__(self):
        # RegEx para CNJ: \b\d{7}[-.]\d{2}[-.]\d{4}[-.]\d[-.]\d{2}[-.]\d{4}\b ou puramente numérico com 20 dígitos
        self._regex_cnj = re.compile(
            r"\b\d{7}[-.]\d{2}[-.]\d{4}[-.]\d[-.]\d{2}[-.]\d{4}\b|\b\d{20}\b"
        )
        
        # RegEx para Valor da Causa (captura variações comuns de termos e formatações financeiras)
        self._regex_valor_causa = re.compile(
            r"(?:valor\s+da\s+causa|dá-se\s+à\s+causa\s+o\s+valor|atribui-se\s+à\s+causa\s+o\s+valor|dá-se\s+à\s+presente\s+o\s+valor)\s*(?::|de)?\s*(?:r\$\s*)?([\d\.,]+)",
            re.IGNORECASE
        )
        
        # RegEx para OAB (inscrições de advogados em diversos estados)
        self._regex_oab = re.compile(
            r"\boab\s*[-/]?\s*[a-z]{2}\s*(?::|\.)?\s*[\d\.\-]+\b",
            re.IGNORECASE
        )
        
        # RegEx para CPF e CNPJ
        self._regex_cnpj = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
        self._regex_cpf = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
        
        # Palavras-chave para Segredo de Justiça / Sigilo
        self._sigilo_keywords = [
            "segredo de justiça", "segredo de justica", "sob sigilo", 
            "sigiloso", "sigilosa", "autos sigilosos", "sigilo processual"
        ]

        # Padrões comuns para identificar partes nas linhas
        self._partes_patterns = [
            (re.compile(r"^\s*(?:autor|requerente|exequente|impetrante|recorrente|reclamante)\s*(?::|-)\s*(.+)$", re.IGNORECASE), "Autor"),
            (re.compile(r"^\s*(?:réu|requerido|executado|impetrado|recorrido|reclamado)\s*(?::|-)\s*(.+)$", re.IGNORECASE), "Réu"),
        ]

        # Tribunais brasileiros mapeados
        self._tribunais_keywords = [
            ("SUPREMO TRIBUNAL FEDERAL", "STF"),
            ("STF", "STF"),
            ("SUPERIOR TRIBUNAL DE JUSTIÇA", "STJ"),
            ("STJ", "STJ"),
            ("TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO", "TJSP"),
            ("TJSP", "TJSP"),
            ("TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO DE JANEIRO", "TJRJ"),
            ("TJRJ", "TJRJ"),
            ("TRIBUNAL DE JUSTIÇA DO ESTADO DE MINAS GERAIS", "TJMG"),
            ("TJMG", "TJMG"),
            ("TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO GRANDE DO SUL", "TJRS"),
            ("TJRS", "TJRS"),
            ("TRIBUNAL DE JUSTIÇA DO ESTADO DO PARANÁ", "TJPR"),
            ("TJPR", "TJPR"),
            ("TRIBUNAL DE JUSTIÇA DO ESTADO DE PERNAMBUCO", "TJPE"),
            ("TJPE", "TJPE"),
            ("TRIBUNAL DE JUSTIÇA DO ESTADO DO CEARÁ", "TJCE"),
            ("TJCE", "TJCE"),
        ]

    def extrair(self, texto: str) -> Dict[str, Any]:
        """
        Extrai metadados estruturados a partir do texto de um documento.
        """
        if not texto:
            return {}

        linhas = [l.strip() for l in texto.split("\n") if l.strip()]

        # 1. Extração do Número do Processo (CNJ)
        cnj_matches = self._regex_cnj.findall(texto)
        processo = ""
        if cnj_matches:
            # Padroniza para exibir o primeiro localizado
            primeiro = cnj_matches[0]
            apenas_digitos = re.sub(r"\D", "", primeiro)
            if len(apenas_digitos) == 20:
                n = apenas_digitos
                processo = f"{n[:7]}-{n[7:9]}.{n[9:13]}.{n[13]}.{n[14:16]}.{n[16:20]}"
            else:
                processo = primeiro

        # 2. Extração do Valor da Causa
        valor_causa = ""
        valor_matches = self._regex_valor_causa.search(texto)
        if valor_matches:
            val_str = valor_matches.group(1).strip()
            # Validação simples para evitar falsos positivos (ex: capturar número de lei ou artigo)
            # Valor de causa geralmente termina com pontuação de milhares/centavos e não tem muitas letras
            if val_str and len(val_str) > 2 and ("," in val_str or "." in val_str or val_str.isdigit()):
                # Se não tem cifrão ou formatação, adicionamos para ficar elegante
                val_str = re.sub(r"[^\d\.,]", "", val_str).rstrip(".,")
                if val_str:
                    valor_causa = f"R$ {val_str}"

        # 3. Inscrições OAB
        oab_matches = self._regex_oab.findall(texto)
        oabs_unicas = []
        for o in oab_matches:
            m = re.match(r"oab\s*[-/]?\s*([a-z]{2})\s*(?::|\.)?\s*([\d\.\-]+)", o, re.IGNORECASE)
            if m:
                uf = m.group(1).upper()
                num = m.group(2)
                norm = f"OAB/{uf} {num}"
                if norm not in oabs_unicas:
                    oabs_unicas.append(norm)

        # 4. CPFs e CNPJs Únicos
        cnpjs_encontrados = list(dict.fromkeys(self._regex_cnpj.findall(texto)))
        cpfs_encontrados = list(dict.fromkeys(self._regex_cpf.findall(texto)))

        # 5. Detecção de Segredo de Justiça
        segredo = "Não"
        texto_low = texto.lower()
        if any(kw in texto_low for kw in self._sigilo_keywords):
            segredo = "Sim"

        # 6. Mapeamento de Partes via varredura de linhas
        partes = {}
        for linha in linhas[:120]:  # Limita a busca ao topo do documento para maior acurácia e velocidade
            for regex, tipo in self._partes_patterns:
                m = regex.match(linha)
                if m:
                    nome = m.group(1).strip().strip(".-: ")
                    # Remover CPFs/CNPJs ou termos indesejados da string do nome
                    nome_limpo = re.sub(r"\s*\(?\s*(?:cpf|cnpj)?\s*\b\d{3}\.\d{3}\.\d{3}-\d{2}\b\s*\)?", "", nome, flags=re.IGNORECASE)
                    nome_limpo = re.sub(r"\s*\(?\s*(?:cpf|cnpj)?\s*\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b\s*\)?", "", nome_limpo, flags=re.IGNORECASE)
                    nome_limpo = re.sub(r"\s*[-–(]?\s*(?:cpf|cnpj).*$", "", nome_limpo, flags=re.IGNORECASE)
                    nome_limpo = nome_limpo.strip(" ,.-/()_")
                    if nome_limpo and len(nome_limpo) > 3 and tipo not in partes:
                        partes[tipo] = nome_limpo

        # 7. Detecção do Tribunal de Origem
        tribunal = "Não identificado"
        top_texto = "\n".join(linhas[:30]).upper()  # Analisa as primeiras 30 linhas
        for kw, sigla in self._tribunais_keywords:
            if kw in top_texto:
                tribunal = sigla
                break
        
        if tribunal == "Não identificado" and processo:
            # Tentar inferir pelo número do processo (segmento J e TT)
            # Formato CNJ: NNNNNNN-DD.AAAA.J.TT.OOOO
            parts = processo.split(".")
            if len(parts) >= 5:
                seg_j = parts[2]
                seg_tt = parts[3]
                if seg_j == "1" and seg_tt == "00":
                    tribunal = "STF"
                elif seg_j == "3" and seg_tt == "00":
                    tribunal = "STJ"
                elif seg_j == "8":
                    tj_mapa = {
                        "01": "TJAC", "02": "TJAL", "03": "TJAP", "04": "TJAM",
                        "05": "TJBA", "06": "TJCE", "07": "TJDF", "08": "TJES",
                        "09": "TJGO", "10": "TJMA", "11": "TJMT", "12": "TJMS",
                        "13": "TJMG", "14": "TJPA", "15": "TJPB", "16": "TJPR",
                        "17": "TJPE", "18": "TJPI", "19": "TJRJ", "20": "TJRN",
                        "21": "TJRS", "22": "TJRO", "23": "TJRR", "24": "TJSC",
                        "25": "TJSE", "26": "TJSP", "27": "TJTO",
                    }
                    tribunal = tj_mapa.get(seg_tt, f"TJ-{seg_tt}")

        # 8. Comarca (varredura do início do arquivo buscando e.g. "FORO DE ...", "COMARCA DE ...")
        comarca = ""
        for linha in linhas[:20]:
            linha_up = linha.upper()
            if "FORO DE" in linha_up or "FORO CENTRAL" in linha_up:
                match = re.search(r"FORO\s+(?:DE\s+|CENTRAL\s+DE\s+)?([A-ZÀ-Ú\s]+)", linha_up)
                if match:
                    comarca = match.group(1).strip()
                    break
            elif "COMARCA DE" in linha_up:
                match = re.search(r"COMARCA\s+DE\s+([A-ZÀ-Ú\s]+)", linha_up)
                if match:
                    comarca = match.group(1).strip()
                    break
        
        # Se comarca não encontrada mas tribunal for TJSP, RJ, etc., usar sigla do estado
        if not comarca and tribunal.startswith("TJ"):
            comarca = tribunal[2:]

        # 9. Datas importantes (procurar datas de assinatura como "São Paulo, 15 de maio de 2026")
        data_doc = ""
        regex_data = re.compile(
            r"\b\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}\b",
            re.IGNORECASE
        )
        data_matches = regex_data.findall(texto)
        if data_matches:
            data_doc = data_matches[-1].strip()  # Pega a última data geralmente no encerramento

        return {
            "numero_processo":    processo or "Não identificado",
            "tribunal":           tribunal,
            "valor_causa":        valor_causa or "Não informado",
            "advogados_oab":      oabs_unicas[:5],  # Limita as primeiras 5 oabs
            "cnpjs":              cnpjs_encontrados[:5],
            "cpfs":               cpfs_encontrados[:5],
            "segredo_justica":    segredo,
            "partes":             partes,
            "comarca":            comarca.title() if comarca else "Não identificada",
            "data_documento":     data_doc or "Não identificada",
        }
