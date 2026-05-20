# src/gerar_relatorio.py
import os
import io
from datetime import datetime
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
    "ALTO":   VERMELHO,
    "MÉDIO":  AMARELO,
    "BAIXO":  VERDE,
}

def gerar_relatorio(
    texto: str,
    classe: str,
    confianca: float,
    probabilidades: dict,
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
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm,
    )

    W, _ = A4
    largura = W - 4*cm

    # ─── Estilos ──────────────────────────────────────────────────────────────
    estilos = getSampleStyleSheet()

    titulo_pg = ParagraphStyle("titulo_pg",
        fontSize=22, fontName="Helvetica-Bold",
        textColor=AZUL_ESCURO, alignment=TA_CENTER, spaceAfter=4)

    subtitulo_pg = ParagraphStyle("subtitulo_pg",
        fontSize=11, fontName="Helvetica",
        textColor=CINZA_TEXTO, alignment=TA_CENTER, spaceAfter=2)

    secao = ParagraphStyle("secao",
        fontSize=13, fontName="Helvetica-Bold",
        textColor=AZUL_ESCURO, spaceBefore=16, spaceAfter=8,
        borderPad=4)

    corpo = ParagraphStyle("corpo",
        fontSize=10, fontName="Helvetica",
        textColor=CINZA_TEXTO, spaceAfter=4, leading=16)

    rodape_style = ParagraphStyle("rodape",
        fontSize=8, fontName="Helvetica",
        textColor=CINZA_TEXTO, alignment=TA_CENTER)

    # ─── Conteúdo ─────────────────────────────────────────────────────────────
    historia = []

    # Cabeçalho
    historia.append(Spacer(1, 0.3*cm))
    historia.append(Paragraph("⚖️ Edge AI Jurídico", titulo_pg))
    historia.append(Paragraph("Relatório de Análise de Documento", subtitulo_pg))
    historia.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}",
        subtitulo_pg
    ))
    historia.append(Spacer(1, 0.3*cm))
    historia.append(HRFlowable(width=largura, thickness=2,
                                color=AZUL_ESCURO, spaceAfter=12))

    # ── 1. Informações do documento ───────────────────────────────────────────
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
        ("BACKGROUND",   (0, 1), (-1, -1), CINZA_CLARO),
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

    # ── 2. Resultado da classificação ─────────────────────────────────────────
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

    # Probabilidades por classe (Gráfico Dinâmico Injectado via RAM)
    historia.append(Paragraph("Probabilidades por classe (Gráfico de Confiança):", corpo))
    
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 2.2), facecolor='white')
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#dee2e6')

    prob_ordenadas = sorted(probabilidades.items(), key=lambda x: -x[1])
    nomes_cls = [c[0].upper() for c in prob_ordenadas]
    valores_prob = [c[1] * 100 for c in prob_ordenadas]
    
    plt_cores = {"lgpd": "#8e44ad", "acordao": "#2980b9", "contrato": "#27ae60", "peticao": "#e67e22", "outro": "#7f8c8d"}
    cores_plot = [plt_cores.get(c[0], "#7f8c8d") for c in prob_ordenadas]

    bars = ax.barh(nomes_cls, valores_prob, color=cores_plot, height=0.6)
    ax.invert_yaxis()
    
    for bar in bars:
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                f'{bar.get_width():.1f}%', va='center', ha='left', fontsize=9, fontweight='bold', color='#555555')
                
    ax.set_xlim(0, 105)
    ax.xaxis.grid(True, linestyle='--', alpha=0.3)
    ax.tick_params(axis='y', length=0, labelsize=9)
    ax.tick_params(axis='x', colors='#555555', labelsize=8)
    
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    
    from reportlab.platypus import Image
    grafico_img = Image(buf, width=15*cm, height=4.7*cm)
    historia.append(grafico_img)
    historia.append(Spacer(1, 0.4*cm))

    # ── 3. Score LGPD e entidades ─────────────────────────────────────────────
    historia.append(Paragraph("3. Análise LGPD e Parecer Executivo", secao))

    risco     = relatorio_ner["risco"]
    score     = relatorio_ner["score_lgpd"]
    n_pessoais = relatorio_ner["dados_pessoais"]
    n_total   = relatorio_ner["total_entidades"]
    cor_risco = CORES_RISCO.get(risco, CINZA_MED)
    
    # Gerar Resumo Executivo Dinâmico
    if risco == "ALTO":
        parecer = "<b>ALERTA CRÍTICO:</b> O documento possui uma alta concentração de dados pessoais (como CPFs, RGs ou similares). A Lei Geral de Proteção de Dados (LGPD) exige que este documento seja mantido em sigilo estrutural ou que sofra anonimização (tarja) antes de publicações ou compartilhamentos."
    elif risco == "MÉDIO":
        parecer = "<b>ALERTA MODERADO:</b> Foi detectada a presença de alguns dados de identificação. Verifique se o contexto de uso requer anonimização de partes das entidades sensíveis sob as diretrizes da LGPD."
    else:
        parecer = "<b>RISCO BAIXO:</b> Nenhuma concentração significativa de dados pessoais foi detectada. O tráfego e armazenamento deste documento apresenta baixo risco à privacidade das partes associadas, condizendo com segurança padrão."
        
    historia.append(Paragraph(parecer, ParagraphStyle("parecer", fontSize=9, fontName="Helvetica", textColor=cor_risco, backColor=CINZA_CLARO, borderPad=6, borderWidth=1, borderColor=cor_risco, leading=14)))
    historia.append(Spacer(1, 0.4*cm))

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
        ("BACKGROUND", (0, 1), (0, 1), cor_risco),
        ("BACKGROUND", (1, 1), (1, 1), cor_risco),
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

    # Tabela de entidades detectadas
    if relatorio_ner["entidades"]:
        historia.append(Paragraph("Entidades extraídas:", corpo))

        from src.ner_juridico import PADROES
        dados_ent = [["Tipo", "LGPD", "Ocorrências", "Valores"]]
        for tipo, valores in relatorio_ner["entidades"].items():
            lgpd_flag = "SIM" if PADROES[tipo]["lgpd"] else "Nao"
            desc      = PADROES[tipo]["descricao"]
            vals_str  = ", ".join(valores[:3])
            if len(valores) > 3:
                vals_str += f" (+{len(valores)-3})"
            dados_ent.append([
                f"{tipo}\n{desc}",
                lgpd_flag,
                str(len(valores)),
                vals_str,
            ])

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
        # Colorir células LGPD=SIM de vermelho suave
        for i, (tipo, _) in enumerate(relatorio_ner["entidades"].items(), 1):
            if PADROES[tipo]["lgpd"]:
                estilos_ent.append(("BACKGROUND", (1, i), (1, i), colors.HexColor("#ffe5e5")))
                estilos_ent.append(("TEXTCOLOR",  (1, i), (1, i), VERMELHO))
                estilos_ent.append(("FONTNAME",   (1, i), (1, i), "Helvetica-Bold"))

        tabela_ent.setStyle(TableStyle(estilos_ent))
        historia.append(tabela_ent)
    else:
        historia.append(Paragraph(
            "Nenhuma entidade juridica foi detectada neste documento.",
            corpo
        ))

    historia.append(Spacer(1, 0.4*cm))

    # ── 4. Trecho do texto analisado ──────────────────────────────────────────
    historia.append(Paragraph("4. Trecho do Texto Analisado", secao))

    trecho = texto[:800].strip()
    if len(texto) > 800:
        trecho += "..."

    historia.append(Paragraph(
        trecho.replace("\n", "<br/>"),
        ParagraphStyle("trecho",
            fontSize=8, fontName="Courier",
            textColor=CINZA_TEXTO, backColor=CINZA_CLARO,
            borderPad=8, borderWidth=0.5, borderColor=CINZA_MED,
            leading=13, spaceAfter=4)
    ))
    historia.append(Spacer(1, 0.4*cm))

    # ── 5. Sobre o modelo ─────────────────────────────────────────────────────
    historia.append(Paragraph("5. Sobre o Modelo Edge AI", secao))

    dados_modelo = [
        ["Parametro", "Valor"],
        ["Arquitetura",     "Dense Neural Network (TF-IDF + Dense)"],
        ["Otimizacao",      "Quantizacao INT8"],
        ["Tamanho",         "796 KB (reducao de 92% vs modelo original)"],
        ["Latencia",        f"{ms_inferencia:.3f} ms por inferencia"],
        ["Throughput",      "25.000+ inferencias por segundo"],
        ["Privacidade",     "100% on-device — dados nao saem do dispositivo"],
        ["Conformidade",    "Pipeline compativel com LGPD (Lei 13.709/2018)"],
        ["Framework",       "TensorFlow Lite 2.15"],
        ["Projeto",         "PIC UNISSAU — Prof. Msc. Afonso Calabria"],
    ]
    tabela_modelo = Table(dados_modelo, colWidths=[5*cm, largura - 5*cm])
    tabela_modelo.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), AZUL_ESCURO),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("FONTNAME",       (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 1), (-1, -1), 9),
        ("FONTNAME",       (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",      (0, 1), (0, -1), AZUL_ESCURO),
        ("GRID",           (0, 0), (-1, -1), 0.5, CINZA_MED),
        ("PADDING",        (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    historia.append(tabela_modelo)
    historia.append(Spacer(1, 0.8*cm))

    # ── Rodapé ────────────────────────────────────────────────────────────────
    historia.append(HRFlowable(width=largura, thickness=1,
                                color=CINZA_MED, spaceBefore=8))
    historia.append(Paragraph(
        f"Edge AI Juridico · PIC UNISSAU · Prof. Msc. Afonso Calabria · "
        f"Gerado em {datetime.now().strftime('%d/%m/%Y as %H:%M')}",
        rodape_style
    ))

    doc.build(historia)
    return buffer.getvalue()


# ─── Teste standalone ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.ner_juridico import NERJuridico

    texto_teste = """
    Exmo. Sr. Juiz, João Silva, CPF 123.456.789-09, OAB/SP 98765,
    vem propor ação de indenização por danos morais contra ACME LTDA,
    CNPJ 12.345.678/0001-99, conforme artigo 186 do Código Civil,
    Lei 10.406/2002. Processo nº 0001234-56.2024.8.26.0100.
    Dá-se à causa o valor de R$ 50.000,00. Prazo: 15 dias.
    """

    ner = NERJuridico()
    rel = ner.relatorio(texto_teste)

    pdf_bytes = gerar_relatorio(
        texto=texto_teste,
        classe="peticao",
        confianca=95.8,
        probabilidades={
            "peticao": 0.958, "outro": 0.021,
            "acordao": 0.012, "contrato": 0.005, "lgpd": 0.004
        },
        relatorio_ner=rel,
        ms_inferencia=0.038,
        nome_doc="Petição Inicial — Teste", 
    )

    os.makedirs("models/relatorio", exist_ok=True)
    with open("models/relatorio/relatorio_teste.pdf", "wb") as f:
        f.write(pdf_bytes)

    print(f"Relatorio gerado: models/relatorio/relatorio_teste.pdf")
    print(f"Tamanho: {len(pdf_bytes)/1024:.1f} KB")