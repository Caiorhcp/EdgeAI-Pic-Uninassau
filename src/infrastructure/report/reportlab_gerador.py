# src/infrastructure/report/reportlab_gerador.py
# Adaptador de infraestrutura — geração de relatório PDF com ReportLab
# Wrapper para manter compatibilidade com app.py e oferecer a função gerar_relatorio()

import os
import io
from datetime import datetime
from typing import Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ─── Paleta de cores ──────────────────────────────────────────────────────────
AZUL_ESCURO  = colors.HexColor("#1a1a2e")
AZUL_MED     = colors.HexColor("#2980b9")
ROXO         = colors.HexColor("#8e44ad")
VERDE        = colors.HexColor("#27ae60")
LARANJA      = colors.HexColor("#e67e22")
CINZA_CLARO  = colors.HexColor("#f8f9fa")
CINZA_MED    = colors.HexColor("#dee2e6")
CINZA_TEXTO  = colors.HexColor("#555555")
VERMELHO     = colors.HexColor("#e74c3c")
AMARELO      = colors.HexColor("#f39c12")

CORES_CLASSE = {
    "lgpd":     ROXO,
    "acordao":  AZUL_MED,
    "contrato": VERDE,
    "peticao":  LARANJA,
    "outro":    colors.HexColor("#7f8c8d"),
}

CORES_RISCO = {
    "ALTO":  VERMELHO,
    "MÉDIO": AMARELO,
    "BAIXO": VERDE,
}


def gerar_relatorio(
    texto: str,
    classe: str,
    confianca: float,
    probabilidades: Dict[str, float],
    relatorio_ner: dict,
    ms_inferencia: float,
    nome_arquivo: str = "relatorio_analise.pdf",
    nome_doc: str = "Documento Jurídico",
) -> bytes:
    """
    Gera um relatório PDF completo com os resultados da análise.
    Retorna os bytes do PDF para download ou salvamento.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    W, _ = A4
    largura = W - 4*cm
    estilos = getSampleStyleSheet()

    titulo_pg = ParagraphStyle("titulo_pg", fontSize=22, fontName="Helvetica-Bold",
        textColor=AZUL_ESCURO, alignment=TA_CENTER, spaceAfter=4)
    subtitulo_pg = ParagraphStyle("subtitulo_pg", fontSize=11, fontName="Helvetica",
        textColor=CINZA_TEXTO, alignment=TA_CENTER, spaceAfter=2)
    secao = ParagraphStyle("secao", fontSize=13, fontName="Helvetica-Bold",
        textColor=AZUL_ESCURO, spaceBefore=16, spaceAfter=8, borderPad=4)
    corpo = ParagraphStyle("corpo", fontSize=10, fontName="Helvetica",
        textColor=CINZA_TEXTO, spaceAfter=4, leading=16)
    rodape_style = ParagraphStyle("rodape", fontSize=8, fontName="Helvetica",
        textColor=CINZA_TEXTO, alignment=TA_CENTER)

    historia = []
    historia.append(Spacer(1, 0.3*cm))
    historia.append(Paragraph("⚖️ Edge AI Jurídico", titulo_pg))
    historia.append(Paragraph("Relatório de Análise de Documento", subtitulo_pg))
    historia.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}", subtitulo_pg))
    historia.append(Spacer(1, 0.3*cm))
    historia.append(HRFlowable(width=largura, thickness=2, color=AZUL_ESCURO, spaceAfter=12))

    # ── 1. Informações do documento
    historia.append(Paragraph("1. Informações do Documento", secao))
    cor_classe = CORES_CLASSE.get(classe, CINZA_MED)
    dados_doc = [
        ["Campo", "Valor"],
        ["Documento analisado", nome_doc],
        ["Data da análise", datetime.now().strftime("%d/%m/%Y %H:%M")],
        ["Caracteres extraídos", f"{len(texto):,}"],
        ["Modelo utilizado", "TFLite INT8 — Edge AI"],
        ["Tempo de inferência", f"{ms_inferencia:.3f} ms"],
    ]
    tabela_doc = Table(dados_doc, colWidths=[5*cm, largura - 5*cm])
    tabela_doc.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), AZUL_ESCURO),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("GRID",         (0, 0), (-1, -1), 0.5, CINZA_MED),
        ("PADDING",      (0, 0), (-1, -1), 6),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",     (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",    (0, 1), (0, -1), AZUL_ESCURO),
    ]))
    historia.append(tabela_doc)
    historia.append(Spacer(1, 0.4*cm))

    # ── 2. Classificação
    historia.append(Paragraph("2. Classificação do Documento", secao))
    classe_upper = classe.upper()
    conf_str     = f"{confianca:.1f}%"
    dados_clf = [
        ["Classe detectada", "Confiança", "Status"],
        [classe_upper, conf_str,
         "Alta confiança" if confianca >= 70 else
         "Confiança moderada" if confianca >= 40 else "Baixa confiança"],
    ]
    tabela_clf = Table(dados_clf, colWidths=[largura/3]*3)
    tabela_clf.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), AZUL_ESCURO),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 10),
        ("BACKGROUND",  (0, 1), (0, 1), cor_classe),
        ("TEXTCOLOR",   (0, 1), (0, 1), colors.white),
        ("FONTNAME",    (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 1), (-1, 1), 14),
        ("BACKGROUND",  (1, 1), (-1, 1), CINZA_CLARO),
        ("GRID",        (0, 0), (-1, -1), 0.5, CINZA_MED),
        ("PADDING",     (0, 0), (-1, -1), 10),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    historia.append(tabela_clf)
    historia.append(Spacer(1, 0.3*cm))

    historia.append(Paragraph("Probabilidades por classe:", corpo))
    prob_ordenadas = sorted(probabilidades.items(), key=lambda x: -x[1])
    dados_prob = [["Classe", "Probabilidade", "Barra"]]
    for cls, prob in prob_ordenadas:
        barra    = "█" * int(prob * 20) + "░" * (20 - int(prob * 20))
        destaque = " ◄" if cls == classe else ""
        dados_prob.append([f"{cls.upper()}{destaque}", f"{prob*100:.1f}%", barra])
    tabela_prob = Table(dados_prob, colWidths=[4*cm, 3*cm, largura - 7*cm])
    tabela_prob.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), AZUL_ESCURO),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("FONTNAME",       (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 1), (-1, -1), 9),
        ("FONTNAME",       (2, 1), (2, -1), "Courier"),
        ("TEXTCOLOR",      (2, 1), (2, -1), AZUL_MED),
        ("GRID",           (0, 0), (-1, -1), 0.5, CINZA_MED),
        ("PADDING",        (0, 0), (-1, -1), 5),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    historia.append(tabela_prob)
    historia.append(Spacer(1, 0.4*cm))

    # ── 3. Score LGPD
    historia.append(Paragraph("3. Análise LGPD e Entidades Detectadas", secao))
    risco      = relatorio_ner["risco"]
    score      = relatorio_ner["score_lgpd"]
    n_pessoais = relatorio_ner["dados_pessoais"]
    n_total    = relatorio_ner["total_entidades"]
    cor_risco  = CORES_RISCO.get(risco, CINZA_MED)
    dados_lgpd = [
        ["Score LGPD", "Nível de Risco", "Dados Pessoais", "Total de Entidades"],
        [f"{score}/100", risco, str(n_pessoais), str(n_total)],
    ]
    tabela_lgpd = Table(dados_lgpd, colWidths=[largura/4]*4)
    tabela_lgpd.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (1, 1), cor_risco),
        ("TEXTCOLOR",  (0, 1), (1, 1), colors.white),
        ("BACKGROUND", (2, 1), (-1, 1), CINZA_CLARO),
        ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 1), (-1, 1), 16),
        ("GRID",       (0, 0), (-1, -1), 0.5, CINZA_MED),
        ("PADDING",    (0, 0), (-1, -1), 10),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    historia.append(tabela_lgpd)
    historia.append(Spacer(1, 0.3*cm))

    if relatorio_ner["entidades"]:
        from src.infrastructure.nlp.ner_juridico import PADROES as PADROES_NER
        historia.append(Paragraph("Entidades extraídas:", corpo))
        dados_ent = [["Tipo", "LGPD", "Ocorrências", "Valores"]]
        for tipo, valores in relatorio_ner["entidades"].items():
            padrao = PADROES_NER.get(tipo, {"lgpd": False, "descricao": "Entidade Reconhecida"})
            lgpd_flag = "SIM" if padrao.get("lgpd", False) else "Não"
            desc      = padrao.get("descricao", "Entidade")
            vals_str  = ", ".join(valores[:3])
            if len(valores) > 3:
                vals_str += f" (+{len(valores)-3})"
            dados_ent.append([f"{tipo}\n{desc}", lgpd_flag, str(len(valores)), vals_str])
        col_w = [4*cm, 1.8*cm, 2.2*cm, largura - 8*cm]
        tabela_ent = Table(dados_ent, colWidths=col_w)
        estilos_ent = [
            ("BACKGROUND",     (0, 0), (-1, 0), AZUL_ESCURO),
            ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
            ("FONTNAME",       (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",       (0, 1), (-1, -1), 8),
            ("GRID",           (0, 0), (-1, -1), 0.5, CINZA_MED),
            ("PADDING",        (0, 0), (-1, -1), 5),
            ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ]
        for i, (tipo, _) in enumerate(relatorio_ner["entidades"].items(), 1):
            if PADROES_NER.get(tipo, {}).get("lgpd", False):
                estilos_ent.append(("BACKGROUND", (1, i), (1, i), colors.HexColor("#ffe5e5")))
                estilos_ent.append(("TEXTCOLOR",  (1, i), (1, i), VERMELHO))
                estilos_ent.append(("FONTNAME",   (1, i), (1, i), "Helvetica-Bold"))
        tabela_ent.setStyle(TableStyle(estilos_ent))
        historia.append(tabela_ent)
    historia.append(Spacer(1, 0.4*cm))

    # ── 4. Trecho do texto
    historia.append(Paragraph("4. Trecho do Texto Analisado", secao))
    trecho = texto[:800].strip()
    if len(texto) > 800:
        trecho += "..."
    historia.append(Paragraph(
        trecho.replace("\n", "<br/>"),
        ParagraphStyle("trecho", fontSize=8, fontName="Courier",
            textColor=CINZA_TEXTO, backColor=CINZA_CLARO,
            borderPad=8, borderWidth=0.5, borderColor=CINZA_MED, leading=13, spaceAfter=4)
    ))
    historia.append(Spacer(1, 0.8*cm))

    # ── Rodapé
    historia.append(HRFlowable(width=largura, thickness=1, color=CINZA_MED, spaceBefore=8))
    historia.append(Paragraph(
        f"Edge AI Juridico · PIC UNISSAU · Prof. Msc. Afonso Calabria · "
        f"Gerado em {datetime.now().strftime('%d/%m/%Y as %H:%M')}",
        rodape_style
    ))

    doc.build(historia)
    return buffer.getvalue()
