# app.py — Edge AI Jurídico · Refatorado com Clean Architecture / DDD
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "2"

import streamlit as st
from datetime import datetime

# ─── Camada de Aplicação (Use Cases) ────────────────────────────────────────
from src.application.dtos.documento_input_dto import DocumentoInputDTO
from src.application.use_cases.analisar_documento import AnalisarDocumentoUseCase
from src.application.use_cases.analisar_pdf import AnalisarPDFUseCase

# ─── Camada de Infraestrutura (Adaptadores) ───────────────────────────────────
from src.infrastructure.ml.tflite_classificador import TFLiteClassificador
from src.infrastructure.nlp.ner_juridico import PADROES
from src.infrastructure.report.reportlab_gerador import gerar_relatorio

# ─── Domínio (Value Objects) ──────────────────────────────────────────────────
from src.domain.value_objects.classe_documento import ClasseDocumento
from src.domain.value_objects.severidade import Severidade

st.set_page_config(
    page_title="Edge AI Jurídico",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');
:root {
  --bg:#0d1117;--s1:#161b22;--s2:#1c2230;--border:#2a3344;
  --ink:#e6edf3;--muted:#7d8fa3;--sky:#4aa3df;--sky-a:rgba(74,163,223,.13);
  --gold:#d4a843;--gold-a:rgba(212,168,67,.13);--r:12px;--sh:0 2px 16px rgba(0,0,0,.45);
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--bg)!important;}
.stApp>header{background:transparent!important;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span{color:var(--ink)!important;}
h1,h2,h3,h4{color:var(--ink)!important;}
label{color:var(--ink)!important;}
.stCaption p{color:var(--muted)!important;}
textarea,input[type="text"]{background:var(--s2)!important;color:var(--ink)!important;
  border:1px solid var(--border)!important;border-radius:var(--r)!important;}
textarea:focus,input[type="text"]:focus{border-color:var(--sky)!important;
  box-shadow:0 0 0 2px rgba(74,163,223,.18)!important;}
[data-testid="stFileUploader"]>div{background:var(--s2)!important;
  border:2px dashed var(--border)!important;border-radius:var(--r)!important;}
button[kind="primary"],[data-testid="stBaseButton-primary"]{
  background:linear-gradient(135deg,#163352,#1a4f7a)!important;color:#fff!important;
  border:1px solid var(--sky)!important;border-radius:var(--r)!important;
  font-weight:600!important;box-shadow:0 0 14px rgba(74,163,223,.18)!important;}
button[kind="secondary"],[data-testid="stBaseButton-secondary"]{
  background:var(--s2)!important;color:var(--ink)!important;
  border:1px solid var(--border)!important;border-radius:var(--r)!important;}
[data-baseweb="tab-list"]{background:transparent!important;
  border-bottom:1px solid var(--border)!important;gap:.4rem;}
[data-baseweb="tab"]{background:transparent!important;color:var(--muted)!important;
  border-radius:8px 8px 0 0!important;font-weight:600!important;}
[data-baseweb="tab"][aria-selected="true"]{color:var(--sky)!important;
  background:var(--sky-a)!important;border-bottom:2px solid var(--sky)!important;}
[data-testid="stExpander"]{background:var(--s1)!important;
  border:1px solid var(--border)!important;border-radius:var(--r)!important;}
[data-testid="stExpander"] summary{color:var(--ink)!important;}
[data-testid="stProgressBar"]>div{background:var(--border)!important;}
[data-testid="stProgressBar"]>div>div{background:var(--sky)!important;}
[data-testid="stSlider"] [role="slider"]{background:var(--sky)!important;border-color:var(--sky)!important;}
[data-testid="stAlert"]{background:var(--s2)!important;border-radius:var(--r)!important;}
[data-testid="metric-container"]{background:var(--s1)!important;
  border:1px solid var(--border)!important;border-radius:var(--r)!important;padding:.8rem!important;}
[data-testid="stMetricLabel"] div{color:var(--muted)!important;}
[data-testid="stMetricValue"] div{color:var(--ink)!important;}
[data-testid="stCode"],.stCodeBlock{background:var(--s2)!important;border:1px solid var(--border)!important;}
code{color:var(--sky)!important;}
hr{border-color:var(--border)!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:99px;}

/* ── Componentes customizados ── */
.ej-hero{background:linear-gradient(135deg,#0d1117 0%,#1a2540 55%,#0f2035 100%);
  border:1px solid var(--border);border-radius:16px;padding:2.2rem 2rem 1.8rem;
  margin-bottom:1.4rem;position:relative;overflow:hidden;box-shadow:0 0 60px rgba(74,163,223,.05);}
.ej-hero::before{content:"⚖";position:absolute;right:-10px;top:-30px;
  font-size:13rem;opacity:.05;line-height:1;pointer-events:none;}
.ej-hero::after{content:"";position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,#4aa3df,transparent);opacity:.4;}
.ej-title{font-family:'DM Serif Display',serif;font-size:2.2rem;color:#fff!important;
  margin:0 0 .25rem;letter-spacing:-.5px;}
.ej-sub{color:#7d8fa3!important;font-size:.92rem;margin:0;}
.ej-tag{display:inline-block;background:rgba(212,168,67,.13);color:#d4a843!important;
  border:1px solid rgba(212,168,67,.28);padding:.13rem .65rem;border-radius:20px;
  font-size:.72rem;font-weight:600;margin:.6rem .35rem 0 0;}
.ej-mrow{display:flex;gap:.75rem;flex-wrap:wrap;margin-bottom:1.3rem;}
.ej-mc{flex:1;min-width:110px;background:var(--s1);border:1px solid var(--border);
  border-radius:var(--r);padding:.85rem 1rem;box-shadow:var(--sh);}
.ej-ml{font-size:.68rem;color:#7d8fa3!important;font-weight:600;text-transform:uppercase;letter-spacing:.05em;}
.ej-mv{font-size:1.25rem;font-weight:700;color:#e6edf3!important;margin-top:.12rem;}
.ej-ms{font-size:.68rem;color:#7d8fa3!important;margin-top:.08rem;}
.ej-res{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);
  padding:1.3rem 1.4rem;box-shadow:var(--sh);margin-bottom:.9rem;}
.ej-pill{display:inline-flex;align-items:center;gap:.35rem;padding:.3rem .9rem;
  border-radius:24px;font-size:.77rem;font-weight:700;letter-spacing:.04em;
  text-transform:uppercase;margin-bottom:.5rem;}
.ej-conf{font-family:'DM Serif Display',serif;font-size:2.8rem;line-height:1;font-weight:400;}
.ej-meta{font-size:.72rem;color:#7d8fa3!important;margin-top:.45rem;}
.ej-pb{margin-bottom:.5rem;}
.ej-pbl{display:flex;justify-content:space-between;font-size:.76rem;
  color:#e6edf3!important;margin-bottom:.22rem;}
.ej-pbt{height:5px;background:#2a3344;border-radius:99px;overflow:hidden;}
.ej-pbf{height:100%;border-radius:99px;}
.ej-rcard{background:var(--s1);border:1px solid var(--border);border-left:3px solid var(--sky);
  border-radius:var(--r);padding:1rem 1.2rem;font-size:.9rem;line-height:1.78;
  color:#e6edf3!important;box-shadow:var(--sh);}
.ej-rmeta{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.55rem;}
.ej-chip{background:rgba(74,163,223,.13);color:#4aa3df!important;
  border:1px solid rgba(74,163,223,.2);border-radius:8px;padding:.08rem .45rem;
  font-size:.7rem;font-weight:600;}
.ej-lgpd{display:flex;align-items:center;gap:.75rem;padding:.75rem 1rem;
  border-radius:var(--r);font-size:.86rem;font-weight:500;margin-bottom:.75rem;}
.ej-alto {background:rgba(220,38,38,.1); border:1px solid rgba(220,38,38,.28); color:#fca5a5!important;}
.ej-medio{background:rgba(234,179,8,.09);border:1px solid rgba(234,179,8,.28); color:#fde68a!important;}
.ej-baixo{background:rgba(34,197,94,.09);border:1px solid rgba(34,197,94,.28); color:#86efac!important;}
.ej-badge{display:inline-flex;align-items:center;gap:.28rem;padding:.18rem .6rem;
  border-radius:99px;font-size:.7rem;font-weight:600;}
.ej-bocr{background:rgba(234,179,8,.1);color:#fde68a!important;border:1px solid rgba(234,179,8,.28);}
.ej-bdig{background:rgba(34,197,94,.09);color:#86efac!important;border:1px solid rgba(34,197,94,.28);}
.ej-footer{text-align:center;color:#7d8fa3!important;font-size:.75rem;
  padding:.9rem 0 .4rem;border-top:1px solid var(--border);margin-top:2rem;}

/* ── LGPD Detector ── */
.lgpd-score-box{background:var(--s1);border:1px solid var(--border);
  border-radius:var(--r);padding:1.4rem;text-align:center;margin-bottom:1rem;}
.lgpd-score-num{font-family:'DM Serif Display',serif;font-size:3.5rem;line-height:1;font-weight:400;}
.lgpd-score-label{font-size:.82rem;color:#7d8fa3!important;margin-top:.3rem;}
.lgpd-nivel{display:inline-block;padding:.25rem .9rem;border-radius:20px;
  font-size:.78rem;font-weight:700;margin-top:.5rem;}
.nivel-conforme    {background:rgba(34,197,94,.12);color:#86efac!important;border:1px solid rgba(34,197,94,.28);}
.nivel-parcial     {background:rgba(74,163,223,.12);color:#93c5fd!important;border:1px solid rgba(74,163,223,.28);}
.nivel-atencao     {background:rgba(234,179,8,.1); color:#fde68a!important;border:1px solid rgba(234,179,8,.28);}
.nivel-nao-conforme{background:rgba(220,38,38,.1); color:#fca5a5!important;border:1px solid rgba(220,38,38,.28);}
.viol-card{background:var(--s2);border:1px solid var(--border);
  border-radius:var(--r);padding:1rem 1.2rem;margin-bottom:.75rem;}
.viol-header{display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem;}
.viol-titulo{font-size:.9rem;font-weight:600;color:#e6edf3!important;}
.viol-artigo{font-size:.72rem;color:#7d8fa3!important;margin-bottom:.4rem;}
.viol-desc{font-size:.82rem;color:#c9d1d9!important;margin-bottom:.55rem;line-height:1.6;}
.viol-ev{background:var(--s1);border-left:3px solid #4aa3df;padding:.4rem .7rem;
  border-radius:0 6px 6px 0;font-size:.78rem;color:#7d8fa3!important;
  font-family:monospace;margin-bottom:.5rem;}
.viol-rec{background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.2);
  border-radius:8px;padding:.45rem .75rem;font-size:.79rem;color:#86efac!important;}
.sev-critica{background:rgba(220,38,38,.15);color:#fca5a5!important;
  border:1px solid rgba(220,38,38,.3);padding:.15rem .55rem;border-radius:99px;font-size:.7rem;font-weight:700;}
.sev-alta   {background:rgba(251,146,60,.12);color:#fdba74!important;
  border:1px solid rgba(251,146,60,.28);padding:.15rem .55rem;border-radius:99px;font-size:.7rem;font-weight:700;}
.sev-media  {background:rgba(234,179,8,.1); color:#fde68a!important;
  border:1px solid rgba(234,179,8,.28); padding:.15rem .55rem;border-radius:99px;font-size:.7rem;font-weight:700;}
.sev-baixa  {background:rgba(34,197,94,.09);color:#86efac!important;
  border:1px solid rgba(34,197,94,.25);padding:.15rem .55rem;border-radius:99px;font-size:.7rem;font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ─── Constantes de UI (do domínio via enum) ───────────────────────────────────
CLASSES_INFO = {
    c.value: {"emoji": c.emoji, "cor": c.cor_hex,
               "cor_a": c.cor_hex.replace("#", "rgba(").rstrip(")") + ",.13)",
               "desc": c.descricao}
    for c in ClasseDocumento
}
# Fallback cor_a simplificado
CLASSES_INFO["lgpd"]["cor_a"]     = "rgba(192,132,252,.13)"
CLASSES_INFO["acordao"]["cor_a"]  = "rgba(74,163,223,.13)"
CLASSES_INFO["contrato"]["cor_a"] = "rgba(74,222,128,.11)"
CLASSES_INFO["peticao"]["cor_a"]  = "rgba(251,146,60,.13)"
CLASSES_INFO["outro"]["cor_a"]    = "rgba(148,163,184,.11)"

RISCO = {
    "ALTO":  {"css": "ej-alto",  "icon": "🔴"},
    "MÉDIO": {"css": "ej-medio", "icon": "🟡"},
    "BAIXO": {"css": "ej-baixo", "icon": "🟢"},
}
SEV_CSS  = {s.value: f"sev-{s.name.lower().replace('Í','i').replace('É','e')}" for s in Severidade}
SEV_CSS  = {
    Severidade.CRITICA.value: "sev-critica",
    Severidade.ALTA.value:    "sev-alta",
    Severidade.MEDIA.value:   "sev-media",
    Severidade.BAIXA.value:   "sev-baixa",
}
SEV_ICON = {
    Severidade.CRITICA.value: "🔴",
    Severidade.ALTA.value:    "🟠",
    Severidade.MEDIA.value:   "🟡",
    Severidade.BAIXA.value:   "🟢",
}
NIVEL_CSS = {
    "CONFORME":              "nivel-conforme",
    "PARCIALMENTE CONFORME": "nivel-parcial",
    "ATENÇÃO":               "nivel-atencao",
    "NÃO CONFORME":          "nivel-nao-conforme",
}

EXEMPLOS = {
    "LGPD":     "O titular CPF 123.456.789-09 tem direito à exclusão de seus dados pessoais conforme Lei 13.709/2018. O controlador deve adotar medidas de segurança para proteger dados pessoais de acessos não autorizados. A ANPD pode aplicar sanções administrativas que vão desde advertência até multa de dois por cento do faturamento. O encarregado pelo tratamento de dados pessoais atuará como canal de comunicação com a ANPD.",
    "Acórdão":  "ACÓRDÃO. STJ, Terceira Turma, por unanimidade, negado provimento ao recurso especial, nos termos do voto do relator. A jurisprudência desta Corte é pacífica no sentido de que o prazo prescricional começa a fluir da data do conhecimento do dano. Incide o enunciado da Súmula 7 do STJ quando a pretensão recursal demanda reexame de provas. O dano moral decorrente de inscrição indevida em cadastro de restrição ao crédito é presumido.",
    "Contrato": "Cláusula Primeira: a contratada ACME LTDA CNPJ 12.345.678/0001-99 obriga-se a prestar serviços de consultoria pelo valor de R$ 5.000,00 mensais. O contrato vigorará pelo prazo de doze meses podendo ser renovado mediante aditivo. Em caso de rescisão imotivada a parte infratora pagará multa de trinta por cento do valor total. As partes elegem o foro da comarca de São Paulo para dirimir quaisquer litígios.",
    "Petição":  "Excelentíssimo Senhor Juiz, vem o requerente OAB/SP 12345, propor ação de indenização por danos morais no valor de R$ 50.000,00, conforme artigo 186 do Código Civil. O réu agiu com manifesta má-fé causando danos ao autor. Requer a citação da parte ré para contestar no prazo legal. Protesta pela produção de todas as provas em direito admitidas.",
    "Outro":    "O princípio da dignidade da pessoa humana, previsto no artigo 1 da Constituição Federal, é fundamento da República Federativa do Brasil. O contraditório e a ampla defesa são garantias fundamentais do processo democrático. A coisa julgada torna imutável e indiscutível a decisão de mérito não mais sujeita a recurso. O mandado de segurança protege direito líquido e certo não amparado por habeas corpus.",
}

# ─── Inicialização dos Use Cases (singleton via cache) ───────────────────────
@st.cache_resource(show_spinner="Carregando modelo TFLite…")
def _inicializar():
    classificador    = TFLiteClassificador()
    analisar_doc_uc  = AnalisarDocumentoUseCase(classificador)
    analisar_pdf_uc  = AnalisarPDFUseCase(classificador)
    return analisar_doc_uc, analisar_pdf_uc

analisar_doc_uc, analisar_pdf_uc = _inicializar()

# ─── Session state ────────────────────────────────────────────────────────────
for k, v in {
    "resultado_pdf": None, "resultado_texto": None,
    "n_frases_pdf": 4, "n_frases_texto": 4, "texto_input": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Helpers de UI ────────────────────────────────────────────────────────────
def H(html): st.markdown(html, unsafe_allow_html=True)


def _barras(probs: dict, classe_top: str):
    html = ""
    for cls, pct_float in sorted(probs.items(), key=lambda x: -x[1]):
        info = CLASSES_INFO[cls]
        pct  = pct_float * 100
        bold = "font-weight:700" if cls == classe_top else "color:#7d8fa3"
        html += (f'<div class="ej-pb"><div class="ej-pbl">'
                 f'<span style="{bold}">{info["emoji"]} {cls.upper()}</span>'
                 f'<span style="{bold}">{pct:.1f}%</span></div>'
                 f'<div class="ej-pbt"><div class="ej-pbf" style="width:{pct:.1f}%;background:{info["cor"]}"></div>'
                 f'</div></div>')
    H(html)


def _secao_resumo(resumo: dict, chave: str):
    st.markdown("#### 📝 Resumo automático")
    nk = f"n_frases_{chave}"
    n  = st.slider("Frases no resumo:", 2, 8, value=st.session_state[nk], key=f"sl_{chave}")
    st.session_state[nk] = n
    if resumo["n_original"] > 0:
        comp = 100 - resumo["taxa_compressao"]
        H(f'<div class="ej-rmeta">'
          f'<span class="ej-chip">{resumo["n_original"]} → {resumo["n_resumo"]} frases</span>'
          f'<span class="ej-chip">{comp:.0f}% de compressão</span>'
          f'<span class="ej-chip">100% local</span></div>'
          f'<div class="ej-rcard">{resumo["resumo"]}</div>')
    else:
        st.info("Texto muito curto para sumarizar.")


def _secao_ner(rel: dict):
    st.markdown("#### 🔍 Entidades detectadas — NER Jurídico")
    risco = rel["risco"]
    cfg   = RISCO[risco]
    H(f'<div class="ej-lgpd {cfg["css"]}">'
      f'{cfg["icon"]} &nbsp;<strong>Score LGPD: {rel["score_lgpd"]}/100</strong>'
      f' &nbsp;·&nbsp; Risco <strong>{risco}</strong>'
      f' &nbsp;·&nbsp; {rel["dados_pessoais"]} dado(s) pessoal(is)</div>')
    if rel["entidades"]:
        cols = st.columns(2)
        for i, (tipo_ner, vals) in enumerate(rel["entidades"].items()):
            tag = " 🔒" if PADROES.get(tipo_ner, {}).get("lgpd", False) else ""
            with cols[i % 2].expander(f"{tipo_ner}{tag} — {len(vals)} ocorrência(s)"):
                for v in vals: st.code(v)
    else:
        st.info("Nenhuma entidade jurídica detectada.")


def _secao_detector_lgpd(analise: dict):
    st.markdown("#### 🛡️ Detector de Violações LGPD")
    score = analise["score_conformidade"]
    nivel = analise["nivel"]
    cor_score = "#86efac" if score >= 90 else "#93c5fd" if score >= 70 else "#fde68a" if score >= 40 else "#fca5a5"
    nivel_css = NIVEL_CSS.get(nivel, "nivel-atencao")
    H(f'<div class="lgpd-score-box">'
      f'<div class="lgpd-score-num" style="color:{cor_score}">{score}</div>'
      f'<div class="lgpd-score-label">Score de Conformidade LGPD / 100</div>'
      f'<div><span class="lgpd-nivel {nivel_css}">{nivel}</span></div>'
      f'</div>')
    if analise["total"] > 0:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Críticas", analise["criticas"])
        c2.metric("🟠 Altas",    analise["altas"])
        c3.metric("🟡 Médias",   analise["medias"])
        c4.metric("🟢 Baixas",   analise["baixas"])
        st.divider()
        st.markdown(f"**{analise['total']} violação(ões) detectada(s):**")
        
        st.markdown("**Análise Relacional por Bloco Jurídico (Context Binding):**")
        for b in analise.get("blocos_detalhados", []):
            with st.expander(f"⚖️ {b['tipo']} — Score do Bloco: {b['score']}/100", expanded=True):
                for v in b["violacoes"]:
                    sev_val  = v.severidade.value if hasattr(v.severidade, 'value') else str(v.severidade)
                    sev_css  = SEV_CSS.get(sev_val, "sev-media")
                    sev_icon = SEV_ICON.get(sev_val, "🟡")
                    H(f'<div class="viol-card">'
                      f'<div class="viol-header">'
                      f'<span class="lgpd-nivel {sev_css}">{sev_icon} {sev_val}</span>'
                      f'<span class="viol-titulo">{v.tipo}</span>'
                      f'</div>'
                      f'<div class="viol-artigo">📖 {v.artigo}</div>'
                      f'<div class="viol-desc">{v.descricao}</div>'
                      f'<div class="viol-ev">📌 Evidência: {v.evidencia}</div>'
                      f'<div class="viol-rec">✅ Recomendação: {v.recomendacao}</div>'
                      f'</div>')
    else:
        H('<div class="ej-lgpd ej-baixo">'
          '🟢 &nbsp;<strong>Nenhuma violação LGPD detectada</strong>'
          ' &nbsp;·&nbsp; Documento em conformidade com os critérios analisados.'
          '</div>')


def exibir_resultado(res, chave: str):
    """Exibe o resultado completo de uma análise."""
    classe    = res.classe
    confianca = res.confianca
    info      = CLASSES_INFO[classe]

    if   res.tipo_extracao == "escaneado": badge = '<span class="ej-badge ej-bocr">📷 OCR aplicado</span>'
    elif res.tipo_extracao == "digital":   badge = '<span class="ej-badge ej-bdig">📄 PDF digital</span>'
    else:                                   badge = ""

    H(f'<div class="ej-res">'
      f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.5rem">'
      f'<div><span class="ej-pill" style="background:{info["cor_a"]};color:{info["cor"]}">'
      f'{info["emoji"]} {classe.upper()}</span> {badge}'
      f'<p style="color:#7d8fa3;font-size:.83rem;margin:.3rem 0 0">{info["desc"]}</p></div>'
      f'<div style="text-align:right">'
      f'<div class="ej-conf" style="color:{info["cor"]}">{confianca:.1f}%</div>'
      f'<div style="font-size:.72rem;color:#7d8fa3">de confiança</div></div></div>'
      f'<div class="ej-meta">⚡ {res.ms_inferencia:.3f} ms &nbsp;·&nbsp; TFLite INT8 &nbsp;·&nbsp; Edge AI'
      f'{res.chars_extra}</div></div>')

    with st.expander("📊 Probabilidades por classe", expanded=True):
        _barras(res.probabilidades, classe)

    st.divider()
    _secao_resumo(res.resumo, chave)
    st.divider()
    _secao_ner(res.relatorio_ner)
    st.divider()
    _secao_detector_lgpd(res.analise_lgpd)
    st.divider()

    pdf_bytes = gerar_relatorio(
        texto=res.texto, classe=classe, confianca=confianca,
        probabilidades=res.probabilidades, relatorio_ner=res.relatorio_ner,
        ms_inferencia=res.ms_inferencia, nome_doc=res.nome_doc,
    )
    st.download_button(
        label="📥 Baixar relatório PDF", data=pdf_bytes,
        file_name=f"relatorio_{classe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf", use_container_width=True, key=f"dl_{chave}",
    )

# ─── Hero ─────────────────────────────────────────────────────────────────────
H("""
<div class="ej-hero">
  <p class="ej-title">⚖️ Edge AI Jurídico</p>
  <p class="ej-sub">Classificação inteligente de documentos jurídicos — 100% local, sem envio de dados à nuvem</p>
  <span class="ej-tag">TFLite INT8</span>
  <span class="ej-tag">OCR Tesseract 5</span>
  <span class="ej-tag">NER Jurídico v2.9</span>
  <span class="ej-tag">Score LGPD</span>
  <span class="ej-tag">Detector LGPD</span>
  <span class="ej-tag">Clean Architecture</span>
</div>
""")

H("""
<div class="ej-mrow">
  <div class="ej-mc"><div class="ej-ml">Modelo</div><div class="ej-mv">TFLite INT8</div><div class="ej-ms">Dense Neural Network</div></div>
  <div class="ej-mc"><div class="ej-ml">Tamanho</div><div class="ej-mv">796 KB</div><div class="ej-ms">92% menor que original</div></div>
  <div class="ej-mc"><div class="ej-ml">Latência</div><div class="ej-mv">~0.04 ms</div><div class="ej-ms">Inferência local</div></div>
  <div class="ej-mc"><div class="ej-ml">OCR</div><div class="ej-mv">Tesseract 5</div><div class="ej-ms">PDFs escaneados</div></div>
  <div class="ej-mc"><div class="ej-ml">LGPD</div><div class="ej-mv">9 regras</div><div class="ej-ms">Detector de violações</div></div>
  <div class="ej-mc"><div class="ej-ml">Privacidade</div><div class="ej-mv">100% local</div><div class="ej-ms">Sem nuvem</div></div>
</div>
""")

# ─── Abas ─────────────────────────────────────────────────────────────────────
aba_pdf, aba_texto, aba_sobre = st.tabs([
    "📂 Carregar PDF", "✏️ Digitar texto", "ℹ️ Sobre o projeto"
])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — PDF
# ══════════════════════════════════════════════════════════════════════════════
with aba_pdf:
    col_e, col_d = st.columns([1.2, 1], gap="large")
    with col_e:
        st.subheader("📂 Carregar documento PDF")
        st.caption("Suporta PDFs digitais e escaneados — detecção automática.")
        arquivo = st.file_uploader(
            "Arraste ou selecione um PDF jurídico", type=["pdf"],
            help="Recomendado até 20 MB",
        )
        modo = st.radio(
            "Modo de análise:", ["Documento completo", "Página por página"],
            horizontal=True,
        )
        btn_analisar = st.button(
            "🔍 Analisar PDF", type="primary",
            use_container_width=True, disabled=(arquivo is None),
        )
        if arquivo is None:
            st.session_state["resultado_pdf"] = None

    with col_d:
        st.subheader("🎯 Resultado")
        if btn_analisar and arquivo:
            if modo == "Documento completo":
                with st.spinner("Detectando tipo de PDF…"):
                    tipo = analisar_pdf_uc.detectar_tipo(arquivo)
                    arquivo.seek(0)
                if tipo == "escaneado":
                    st.warning("📷 PDF escaneado — aplicando OCR…")
                else:
                    st.success("📄 PDF digital — extração direta.")
                try:
                    com_spinner = "Aplicando OCR…" if tipo == "escaneado" else "Extraindo texto…"
                    with st.spinner(com_spinner):
                        resultado = analisar_pdf_uc.executar_completo(
                            arquivo, arquivo.name,
                            n_frases=st.session_state["n_frases_pdf"],
                        )
                    st.session_state["resultado_pdf"] = resultado
                    with st.expander("📄 Pré-visualizar texto extraído"):
                        t = resultado.texto
                        st.text_area("", t[:3000] + ("…" if len(t) > 3000 else ""),
                                     height=200, disabled=True)
                except Exception as exc:
                    st.error(f"❌ {exc}")
                    st.session_state["resultado_pdf"] = None
            else:
                with st.spinner("Analisando página por página…"):
                    resultados_pag = analisar_pdf_uc.executar_por_pagina(arquivo, arquivo.name)
                st.session_state["resultado_pdf"] = None
                if not resultados_pag:
                    st.error("❌ Nenhuma página com texto detectável.")
                else:
                    tipo = resultados_pag[0]["resultado"].tipo_extracao or "digital"
                    st.success(f"✅ {len(resultados_pag)} página(s) · {'📷 OCR' if tipo=='escaneado' else '📄 Digital'}")
                    contagem = {}
                    for r in resultados_pag:
                        cls = r["resultado"].classe
                        contagem[cls] = contagem.get(cls, 0) + 1
                    st.markdown("**Distribuição por classe:**")
                    cols_d = st.columns(len(contagem))
                    for col, (cls, qtd) in zip(cols_d, sorted(contagem.items(), key=lambda x: -x[1])):
                        col.metric(f"{CLASSES_INFO[cls]['emoji']} {cls.upper()}", f"{qtd} pág.")
                    st.divider()
                    for item in resultados_pag:
                        res_p = item["resultado"]
                        inf   = CLASSES_INFO[res_p.classe]
                        with st.expander(f"Página {item['pagina']} — {inf['emoji']} {res_p.classe.upper()} ({res_p.confianca:.0f}%)"):
                            st.progress(res_p.confianca / 100, text=f"{res_p.confianca:.1f}%")
                            cfg      = RISCO[res_p.relatorio_ner["risco"]]
                            nivel_css = NIVEL_CSS.get(res_p.analise_lgpd["nivel"], "nivel-atencao")
                            H(f'<div class="ej-lgpd {cfg["css"]}" style="font-size:.8rem">'
                              f'{cfg["icon"]} Score NER: <strong>{res_p.relatorio_ner["score_lgpd"]}/100</strong>'
                              f' &nbsp;·&nbsp; Conformidade: '
                              f'<span class="lgpd-nivel {nivel_css}" style="font-size:.7rem">'
                              f'{res_p.analise_lgpd["score_conformidade"]}/100 {res_p.analise_lgpd["nivel"]}</span>'
                              f' &nbsp;·&nbsp; {res_p.analise_lgpd["total"]} violação(ões)</div>')
                            if res_p.resumo.get("n_original", 0) > 0:
                                st.markdown("**Resumo:**")
                                H(f'<div class="ej-rcard" style="font-size:.84rem">{res_p.resumo["resumo"]}</div>')
                            pdf_p = gerar_relatorio(
                                texto=res_p.texto, classe=res_p.classe, confianca=res_p.confianca,
                                probabilidades=res_p.probabilidades, relatorio_ner=res_p.relatorio_ner,
                                ms_inferencia=res_p.ms_inferencia,
                                nome_doc=f"{arquivo.name} — Página {item['pagina']}",
                            )
                            st.download_button(
                                label=f"📥 Relatório página {item['pagina']}", data=pdf_p,
                                file_name=f"relatorio_p{item['pagina']}_{res_p.classe}.pdf",
                                mime="application/pdf", key=f"dl_p_{item['pagina']}",
                            )

        if st.session_state["resultado_pdf"] is not None and modo == "Documento completo":
            exibir_resultado(st.session_state["resultado_pdf"], chave="pdf")
        elif not btn_analisar and st.session_state["resultado_pdf"] is None and modo == "Documento completo":
            st.info("👈 Carregue um PDF para começar — digital ou escaneado.")

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — Texto manual
# ══════════════════════════════════════════════════════════════════════════════
with aba_texto:
    col_e2, col_d2 = st.columns([1.2, 1], gap="large")
    with col_e2:
        st.subheader("✏️ Insira o texto jurídico")
        st.caption("Cole um trecho ou escolha um exemplo para teste rápido:")
        ex_cols = st.columns(len(EXEMPLOS))
        for col, (label, exemplo) in zip(ex_cols, EXEMPLOS.items()):
            if col.button(label, use_container_width=True, key=f"ex_{label}"):
                st.session_state["texto_input"]    = exemplo
                st.session_state["resultado_texto"] = None
                st.rerun()
        texto = st.text_area(
            "Texto jurídico",
            value=st.session_state.get("texto_input", ""),
            height=240,
            placeholder="Cole ou digite aqui um trecho de documento jurídico…",
            label_visibility="collapsed",
        )
        n_chars = len(texto.strip())
        if n_chars > 0:
            st.caption(f"📏 {n_chars:,} caracteres · {len(texto.split()):,} palavras")
        btn_cls = st.button(
            "🔍 Classificar, resumir, extrair entidades e analisar LGPD",
            type="primary", use_container_width=True, disabled=(n_chars < 10),
        )
    with col_d2:
        st.subheader("🎯 Resultado")
        if btn_cls and n_chars >= 10:
            with st.spinner("Processando e analisando conformidade LGPD…"):
                dto = DocumentoInputDTO(
                    texto=texto,
                    nome="Texto digitado",
                    n_frases_resumo=st.session_state["n_frases_texto"],
                )
                st.session_state["resultado_texto"] = analisar_doc_uc.executar(dto)
        if st.session_state.get("resultado_texto") is not None:
            exibir_resultado(st.session_state["resultado_texto"], chave="texto")
        elif not btn_cls:
            st.info("👈 Insira um texto jurídico e clique em Classificar.")

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — Sobre
# ══════════════════════════════════════════════════════════════════════════════
with aba_sobre:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 🔬 Pipeline completo")
        st.markdown("""
- Detecção automática PDF digital/escaneado
- OCR: Tesseract 5 (português)
- Vetorização: TF-IDF bigramas
- Classificação: Dense NN · TFLite INT8
- Resumo: Sumarização extrativa TF-IDF
- NER: Regex jurídico v2.9 (CPF validado)
- Detector LGPD: 9 regras jurídicas
- Relatório: ReportLab PDF
- **Arquitetura: Clean Architecture / DDD**
        """)
    with c2:
        st.markdown("#### 📂 Classes detectadas")
        for k, v in CLASSES_INFO.items():
            st.markdown(f"{v['emoji']} **{k.upper()}** — {v['desc']}")
    with c3:
        st.markdown("#### 🛡️ Violações LGPD detectadas")
        st.markdown("""
🔴 Dados pessoais sem base legal (Art. 7)
🔴 Dados sensíveis sem proteção (Art. 11)
🟠 Dados de crianças (Art. 14)
🟠 Sem registro de operações (Art. 37)
🟠 Sem medidas de segurança (Art. 46)
🟡 Sem notificação de incidentes (Art. 48)
🟠 Finalidade incompatível (Art. 6)
🟡 Retenção excessiva (Art. 15)
🟠 Transferência internacional (Art. 33)
        """)
    st.divider()
    st.markdown("""
> **Por que Edge AI + Detector LGPD?**  
> Documentos jurídicos contêm dados sensíveis — CPF, CNPJ, saúde, crianças.  
> O detector analisa 9 tipos de violação baseados na Lei 13.709/2018,  
> tudo 100% no dispositivo, sem tráfego para servidores externos.
    """)

H('<div class="ej-footer">PIC — Edge AI Jurídico &nbsp;·&nbsp; Prof. Msc. Afonso Calábria &nbsp;·&nbsp; UNISSAU &nbsp;·&nbsp; 2026</div>')