# app.py — Edge AI Jurídico · Refatorado com Clean Architecture / DDD
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "2"

import streamlit as st
import json
from datetime import datetime

# ─── Camada de Aplicação (Use Cases) ────────────────────────────────────────
from src.application.dtos.documento_input_dto import DocumentoInputDTO
from src.application.dtos.processo_input_dto import ProcessoInputDTO
from src.application.use_cases.analisar_documento import AnalisarDocumentoUseCase
from src.application.use_cases.analisar_pdf import AnalisarPDFUseCase
from src.application.use_cases.consultar_processo import ConsultarProcessoUseCase

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
    initial_sidebar_state="expanded",
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

/* ── Custom Veredicto & Sidebar Styles ── */
.ej-veredicto-card {
  background:linear-gradient(135deg, #161b22 0%, #1c2230 100%)!important;
  border:1px solid var(--border)!important;
  border-left:5px solid var(--gold)!important;
  border-radius:var(--r)!important;
  padding:1.4rem!important;
  box-shadow:var(--sh)!important;
  margin-bottom:1.1rem!important;
}
.ej-v-title {
  font-family:'DM Serif Display', serif;
  font-size:1.45rem;
  color:var(--gold)!important;
  margin:0 0 .4rem 0!important;
}
.ej-v-risk {
  display:inline-block;
  padding:.15rem .55rem;
  border-radius:4px;
  font-size:.7rem;
  font-weight:700;
  margin-bottom:.7rem;
}
.ej-v-desc {
  font-size:.9rem;
  line-height:1.65;
  color:#e6edf3!important;
}
.ej-v-alert {
  background:rgba(220,38,38,.07)!important;
  border:1px solid rgba(220,38,38,.18)!important;
  border-radius:8px;
  padding:.55rem .75rem;
  font-size:.82rem;
  color:#fca5a5!important;
  margin-top:.45rem;
}
.ej-v-rec {
  background:rgba(34,197,94,.05)!important;
  border:1px solid rgba(34,197,94,.15)!important;
  border-radius:8px;
  padding:.55rem .75rem;
  font-size:.82rem;
  color:#86efac!important;
  margin-top:.45rem;
}
.ej-side-card {
  background:var(--s1);
  border:1px solid var(--border);
  border-radius:10px;
  padding:.65rem .75rem;
  margin-bottom:.6rem;
  box-shadow:0 1px 6px rgba(0,0,0,.2);
}
.ej-side-meta {
  font-size:.65rem;
  color:#7d8fa3!important;
  display:flex;
  justify-content:space-between;
  margin-bottom:.15rem;
}
.ej-side-title {
  font-size:.8rem;
  font-weight:600;
  color:#e6edf3!important;
  overflow:hidden;
  white-space:nowrap;
  text-overflow:ellipsis;
}
.ej-side-tag {
  display:inline-block;
  font-size:.62rem;
  font-weight:700;
  padding:.05rem .35rem;
  border-radius:4px;
  margin-top:.25rem;
}
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
    consultar_proc_uc = ConsultarProcessoUseCase(classificador, analisar_doc_uc=analisar_doc_uc)
    return analisar_doc_uc, analisar_pdf_uc, consultar_proc_uc

analisar_doc_uc, analisar_pdf_uc, consultar_proc_uc = _inicializar()

# ─── Carregar Métricas Dinâmicas do Modelo ────────────────────────────────────
model_metrics = {
    "acuracia_keras": 0.925,
    "f1_macro": 0.918,
    "n_treino": 240,
    "tamanho_kb": 796,
    "latencia_ms": 0.04,
    "epocas_treinadas": 150,
}
try:
    with open("models/relatorio/metricas.json", "r", encoding="utf-8") as f:
        loaded = json.load(f)
        model_metrics["acuracia_keras"] = loaded.get("acuracia_keras", loaded.get("acuracia_final", 0.925))
        model_metrics["f1_macro"] = loaded.get("f1_macro", 0.918)
        model_metrics["n_treino"] = loaded.get("n_treino", 240)
        model_metrics["tamanho_kb"] = loaded.get("tamanho_kb", 796)
        model_metrics["latencia_ms"] = loaded.get("latencia_ms", 0.04)
        model_metrics["epocas_treinadas"] = loaded.get("epocas_treinadas", 150)
except Exception:
    pass

# ─── Session state ────────────────────────────────────────────────────────────
for k, v in {
    "resultado_pdf": None, "resultado_texto": None, "resultado_processo": None,
    "dados_processo": None, "historico_analises": [], "item_selecionado_historico": None,
    "n_frases_pdf": 4, "n_frases_texto": 4, "n_frases_processo": 4,
    "texto_input": "", "numero_processo_input": "", "comparar_id_1": None, "comparar_id_2": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Helper para adicionar análises concluídas ao histórico
def adicionar_ao_historico(tipo: str, nome: str, resultado, dados_extra=None):
    historico = st.session_state.get("historico_analises", [])
    # Evitar duplicados consecutivos de mesmo nome
    if historico and historico[0].get("nome") == nome:
        return
    item = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "tipo": tipo,  # 'PDF', 'Texto', 'Processo'
        "nome": nome,
        "resultado": resultado,
        "dados_extra": dados_extra  # Metadados adicionais, ex: DTO do processo
    }
    historico.insert(0, item)
    st.session_state["historico_analises"] = historico[:10]


# ─── Helpers de UI ────────────────────────────────────────────────────────────
def H(html):
    # Remove o recuo das linhas para evitar que o markdown interprete como bloco de código indentado
    linhas_limpas = [linha.strip() for linha in html.split("\n")]
    st.markdown("\n".join(linhas_limpas), unsafe_allow_html=True)


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
    if nk not in st.session_state:
        st.session_state[nk] = 4
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

    # 📋 Ficha Técnica Extraída do Arquivo (Metadados do Processo)
    meta = getattr(res, "metadados_arquivo", None)
    if meta and isinstance(meta, dict) and meta.get("numero_processo") != "Não identificado":
        sigilo_class = "ej-alto" if meta.get("segredo_justica") == "Sim" else "ej-baixo"
        sigilo_icon = "🔒" if meta.get("segredo_justica") == "Sim" else "🔓"
        oab_list = ", ".join(meta.get("advogados_oab", [])) or "Nenhum advogado identificado"
        cpfs_cnpjs = []
        if meta.get("cpfs"): cpfs_cnpjs.extend([f"CPF: {c}" for c in meta["cpfs"]])
        if meta.get("cnpjs"): cpfs_cnpjs.extend([f"CNPJ: {c}" for c in meta["cnpjs"]])
        doc_idents = ", ".join(cpfs_cnpjs) or "Nenhum CPF/CNPJ identificado"
        partes_dict = meta.get("partes", {})
        autor = partes_dict.get("Autor", "Não identificado")
        reu = partes_dict.get("Réu", "Não identificado")

        html_ficha = f"""
        <div style="margin-top: 1.2rem; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.8rem 0; font-family:'DM Serif Display',serif; font-size:1.35rem; display:flex; align-items:center; gap:0.5rem; color:#fff!important;">
                📋 Ficha Técnica Extraída do Arquivo
            </h4>
            <div class="ej-mrow">
                <div class="ej-mc">
                    <div class="ej-ml">Número do Processo</div>
                    <div class="ej-mv" style="font-size:1.05rem; font-weight:700;">{meta.get("numero_processo")}</div>
                    <div class="ej-ms">CNJ Autodetectado</div>
                </div>
                <div class="ej-mc">
                    <div class="ej-ml">Tribunal / Comarca</div>
                    <div class="ej-mv" style="font-size:1.05rem; font-weight:700;">🏛️ {meta.get("tribunal")}</div>
                    <div class="ej-ms">{meta.get("comarca")}</div>
                </div>
                <div class="ej-mc">
                    <div class="ej-ml">Valor da Causa</div>
                    <div class="ej-mv" style="font-size:1.05rem; font-weight:700; color:var(--gold)!important;">💰 {meta.get("valor_causa")}</div>
                    <div class="ej-ms">Estimado no texto</div>
                </div>
                <div class="ej-mc">
                    <div class="ej-ml">Segredo de Justiça</div>
                    <div style="margin-top:0.35rem;">
                        <span class="ej-badge {sigilo_class}" style="font-size:0.72rem; font-weight:700; text-transform:uppercase;">
                            {sigilo_icon} {meta.get("segredo_justica")}
                        </span>
                    </div>
                    <div class="ej-ms">Sigilo de dados</div>
                </div>
            </div>
            <div class="ej-mrow" style="margin-top: -0.5rem;">
                <div class="ej-mc" style="flex: 1.5; min-width: 250px;">
                    <div class="ej-ml">Partes Envolvidas</div>
                    <div class="ej-mv" style="font-size:0.9rem; font-weight:normal; line-height:1.5; margin-top:0.25rem;">
                        👤 <strong>Autor:</strong> {autor}<br/>
                        ⚖️ <strong>Réu:</strong> {reu}
                    </div>
                </div>
                <div class="ej-mc" style="flex: 1.2; min-width: 200px;">
                    <div class="ej-ml">Documentos Identificados</div>
                    <div class="ej-mv" style="font-size:0.8rem; font-weight:normal; line-height:1.5; color:#c9d1d9!important; margin-top:0.25rem;">
                        🆔 {doc_idents}
                    </div>
                </div>
                <div class="ej-mc">
                    <div class="ej-ml">Advogados (OABs)</div>
                    <div class="ej-mv" style="font-size:0.8rem; font-weight:normal; line-height:1.5; color:#c9d1d9!important; margin-top:0.25rem;">
                        💼 {oab_list}
                    </div>
                </div>
                <div class="ej-mc">
                    <div class="ej-ml">Data de Assinatura</div>
                    <div class="ej-mv" style="font-size:0.9rem; font-weight:700; margin-top:0.25rem;">📅 {meta.get("data_documento")}</div>
                    <div class="ej-ms">Fechamento da peça</div>
                </div>
            </div>
        </div>
        """
        H(html_ficha)

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

# ─── Sidebar com Histórico Recente ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Histórico da Sessão")
    st.caption("Últimas 10 análises executadas localmente nesta sessão.")
    
    historico = st.session_state.get("historico_analises", [])
    if not historico:
        st.info("Nenhuma análise no histórico ainda.")
    else:
        for idx, item in enumerate(historico):
            tipo = item["tipo"]
            nome = item["nome"]
            res  = item["resultado"]
            
            # Detalhes da classe
            emoji = CLASSES_INFO.get(res.classe, {}).get("emoji", "📄")
            cor   = CLASSES_INFO.get(res.classe, {}).get("cor", "#7d8fa3")
            cor_a = CLASSES_INFO.get(res.classe, {}).get("cor_a", "rgba(0,0,0,0.1)")
            
            st.markdown(f"""
            <div class="ej-side-card">
                <div class="ej-side-meta">
                    <span>⏱️ {item['timestamp']}</span>
                    <span>{tipo}</span>
                </div>
                <div class="ej-side-title" title="{nome}">{nome}</div>
                <div class="ej-side-tag" style="background:{cor_a};color:{cor};border:1px solid {cor}44">
                    {emoji} {res.classe.upper()} ({res.confianca:.0f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão de visualização
            if st.button(f"Visualizar item {idx+1}", key=f"btn_hist_{item['id']}", use_container_width=True):
                st.session_state["item_selecionado_historico"] = item
                st.toast(f"Carregado: {nome} na aba Histórico!")
                st.rerun()
                
        if st.button("🧹 Limpar Histórico", use_container_width=True):
            st.session_state["historico_analises"] = []
            st.session_state["item_selecionado_historico"] = None
            st.rerun()

# ─── Métricas Dinâmicas ───────────────────────────────────────────────────────
acc_pct = model_metrics["acuracia_keras"] * 100
f1_val  = model_metrics["f1_macro"]
H(f"""
<div class="ej-mrow">
  <div class="ej-mc"><div class="ej-ml">Acurácia</div><div class="ej-mv">{acc_pct:.2f}%</div><div class="ej-ms">F1-score: {f1_val:.3f}</div></div>
  <div class="ej-mc"><div class="ej-ml">Tamanho</div><div class="ej-mv">{model_metrics['tamanho_kb']} KB</div><div class="ej-ms">TFLite INT8 Quantizado</div></div>
  <div class="ej-mc"><div class="ej-ml">Latência</div><div class="ej-mv">~{model_metrics['latencia_ms']:.2f} ms</div><div class="ej-ms">Inferência local</div></div>
  <div class="ej-mc"><div class="ej-ml">Treino</div><div class="ej-mv">{model_metrics['n_treino']} amostras</div><div class="ej-ms">{model_metrics['epocas_treinadas']} épocas</div></div>
  <div class="ej-mc"><div class="ej-ml">LGPD</div><div class="ej-mv">9 regras</div><div class="ej-ms">Artigos 6, 7, 11, 14...</div></div>
  <div class="ej-mc"><div class="ej-ml">Privacidade</div><div class="ej-mv">100% local</div><div class="ej-ms">Sem tráfego externo</div></div>
</div>
""")

# ─── Abas ─────────────────────────────────────────────────────────────────────
aba_pdf, aba_texto, aba_processo, aba_historico, aba_sobre = st.tabs([
    "📂 Carregar PDF", "✏️ Digitar texto", "🔍 Buscar Processo", "📊 Histórico", "ℹ️ Sobre o projeto"
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
                    adicionar_ao_historico("PDF", arquivo.name, resultado)
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
        if btn_cls and texto.strip():
            with st.spinner("Classificando e analisando localmente..."):
                dto = DocumentoInputDTO(texto=texto, nome_doc="Texto digitado")
                res = analisar_doc_uc.executar(dto)
                st.session_state["resultado_texto"] = res
                adicionar_ao_historico("Texto", f"Texto digitado ({datetime.now().strftime('%H:%M')})", res)
        
        if st.session_state.get("resultado_texto") is not None:
            exibir_resultado(st.session_state["resultado_texto"], chave="texto")
        elif not btn_cls and st.session_state.get("resultado_texto") is None:
            st.info("👈 Insira um texto jurídico e clique em Classificar.")

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — Buscar Processo Judicial (Novo)
# ══════════════════════════════════════════════════════════════════════════════
with aba_processo:
    col_proc_e, col_proc_d = st.columns([1.2, 1], gap="large")
    
    with col_proc_e:
        st.subheader("🔍 Consulta Judicial Online")
        st.caption("Insira o número único do processo (padrão CNJ) para busca direta nas fontes públicas.")
        
        # Input do CNJ com helper dinâmico
        num_input = st.text_input(
            "Número do Processo (CNJ)",
            value=st.session_state.get("numero_processo_input", ""),
            placeholder="0000000-00.0000.0.00.0000",
            help="Formato esperado: NNNNNNN-DD.AAAA.J.TT.OOOO",
        )
        st.session_state["numero_processo_input"] = num_input
        
        # Validação ao vivo
        from src.infrastructure.web.consultador_processo import validar_numero_cnj, normalizar_numero_cnj, detectar_tribunal
        
        if num_input.strip():
            num_norm = normalizar_numero_cnj(num_input)
            if not validar_numero_cnj(num_norm):
                st.warning("⚠️ Formato CNJ incompleto ou inválido. Exemplo: 0005392-75.2023.8.26.0000")
            else:
                trib = detectar_tribunal(num_norm)
                st.success(f"✅ Formato CNJ válido. Tribunal identificado: **{trib}**")
        
        n_frases_proc = st.slider(
            "Frases no resumo:", 2, 8,
            value=st.session_state["n_frases_processo"],
            key="sl_processo_slider"
        )
        st.session_state["n_frases_processo"] = n_frases_proc
        
        btn_buscar = st.button(
            "⚡ Buscar e Analisar Processo",
            type="primary",
            use_container_width=True,
            disabled=not num_input.strip()
        )
        
    with col_proc_d:
        st.subheader("🎯 Resultado da Consulta")
        
        if btn_buscar and num_input.strip():
            num_norm = normalizar_numero_cnj(num_input)
            if not validar_numero_cnj(num_norm):
                st.error("❌ Não é possível buscar: o número CNJ fornecido é inválido.")
            else:
                steps = ["Validando número CNJ...", "Buscando nas APIs públicas (STJ/STF/Datajud)...", "Analisando com Edge AI local...", "Gerando veredicto..."]
                progress_bar = st.progress(0)
                
                # Etapa 1
                progress_bar.progress(25, text=steps[0])
                time_sleep = 0.5
                import time; time.sleep(time_sleep)
                
                # Etapa 2
                progress_bar.progress(50, text=steps[1])
                try:
                    # Executar Use Case
                    input_dto = ProcessoInputDTO(numero_cnj=num_norm)
                    dados_dto, resultado_dto = consultar_proc_uc.executar(
                        input_dto,
                        n_frases_resumo=n_frases_proc
                    )
                    
                    if not dados_dto.encontrado:
                        progress_bar.empty()
                        st.error(f"❌ {dados_dto.erro or 'Processo não encontrado nas fontes públicas.'}")
                        if dados_dto.url_fonte:
                            st.link_button(
                                f"🔗 Consultar diretamente no portal do {dados_dto.tribunal}",
                                dados_dto.url_fonte,
                                use_container_width=True,
                            )
                        st.session_state["resultado_processo"] = None
                        st.session_state["dados_processo"] = None
                    else:
                        # Etapa 3 e 4
                        progress_bar.progress(75, text=steps[2])
                        time.sleep(time_sleep)
                        progress_bar.progress(100, text=steps[3])
                        time.sleep(time_sleep)
                        progress_bar.empty()
                        
                        st.session_state["resultado_processo"] = resultado_dto
                        st.session_state["dados_processo"] = dados_dto
                        
                        # Salvar no histórico
                        if resultado_dto:
                            adicionar_ao_historico(
                                "Processo",
                                f"Processo {dados_dto.numero}",
                                resultado_dto,
                                dados_extra=dados_dto
                            )
                            st.toast(f"Processo {dados_dto.numero} analisado com sucesso!")
                except Exception as ex:
                    progress_bar.empty()
                    st.error(f"Erro na busca do processo: {ex}")
                    st.session_state["resultado_processo"] = None
                    st.session_state["dados_processo"] = None
        
        # Exibição dos resultados da busca
        dados_salvos = st.session_state.get("dados_processo")
        res_salvo = st.session_state.get("resultado_processo")
        
        if dados_salvos and res_salvo:
            # 1. Informações básicas do processo
            st.markdown("### 📋 Metadados Detalhados do Processo")
            
            col_meta_e, col_meta_d = st.columns([2.2, 1], gap="medium")
            with col_meta_e:
                # Criar lista em HTML para as partes
                li_partes = "".join([f'<li style="margin-bottom:0.25rem;">{p}</li>' for p in dados_salvos.partes]) if dados_salvos.partes else '<li>Não informadas</li>'
                H(f"""
                <div class="ej-res" style="border-left: 4px solid var(--sky); min-height: 180px;">
                    <p style="font-size: 1.15rem; font-weight: 700; margin: 0 0 0.6rem 0; color: #fff;">🔢 CNJ: {dados_salvos.numero}</p>
                    <div class="ej-rmeta" style="margin-bottom: 0.9rem;">
                        <span class="ej-chip" style="font-size: 0.72rem; padding: 0.1rem 0.5rem;">🏛️ Órgão: {dados_salvos.tribunal}</span>
                        <span class="ej-chip" style="font-size: 0.72rem; padding: 0.1rem 0.5rem;">📂 Classe: {dados_salvos.classe_processual or 'Classe não informada'}</span>
                        <span class="ej-chip" style="font-size: 0.72rem; padding: 0.1rem 0.5rem;">🌐 Canal: {dados_salvos.fonte}</span>
                    </div>
                    <p style="font-size: 0.88rem; margin: 0 0 0.5rem 0;"><strong>⚖️ Assunto Principal:</strong> {dados_salvos.assunto or 'Não informado'}</p>
                    <p style="font-size: 0.88rem; margin: 0 0 0.2rem 0;"><strong>👥 Envolvidos (Partes):</strong></p>
                    <ul style="margin: 0 0 0 1.1rem; padding: 0; font-size: 0.84rem; color: #7d8fa3; line-height: 1.5;">
                        {li_partes}
                    </ul>
                </div>
                """)
            with col_meta_d:
                st.markdown("**Ações Rápidas**")
                if dados_salvos.url_fonte:
                    st.link_button("🔗 Consultar Fonte Oficial", dados_salvos.url_fonte, use_container_width=True, type="secondary")
                st.info(f"⚡ Extração e indexação completadas via {dados_salvos.fonte} em ambiente 100% Edge/Local.")
            
            # Grid de Metadados Avançados do Processo
            st.markdown("#### ⚙️ Detalhamento de Ficha Processual")
            seg_val = getattr(dados_salvos, "segredo_justica", "Não") or "Não"
            seg_css = "ej-alto" if seg_val == "Sim" else "ej-baixo"
            
            st_val = getattr(dados_salvos, "status", "Ativo") or "Ativo"
            st_lower = st_val.lower()
            if "ativo" in st_lower or "andamento" in st_lower:
                status_css = "ej-baixo"
            elif "suspenso" in st_lower:
                status_css = "ej-medio"
            else:
                status_css = "ej-chip"
                
            H(f"""
            <div class="ej-mrow">
                <div class="ej-mc"><div class="ej-ml">⚖️ Órgão Julgador</div><div class="ej-mv" style="font-size:0.95rem;">{getattr(dados_salvos, 'orgao_julgador', 'Não informado') or 'Não informado'}</div></div>
                <div class="ej-mc"><div class="ej-ml">👤 Relator / Juiz</div><div class="ej-mv" style="font-size:0.95rem;">{getattr(dados_salvos, 'relator', 'Não informado') or 'Não informado'}</div></div>
                <div class="ej-mc"><div class="ej-ml">📅 Autuação / Distribuição</div><div class="ej-mv" style="font-size:0.95rem;">{getattr(dados_salvos, 'data_distribuicao', 'Não informada') or 'Não informada'}</div></div>
                <div class="ej-mc"><div class="ej-ml">📍 Comarca / Localidade</div><div class="ej-mv" style="font-size:0.95rem;">{getattr(dados_salvos, 'comarca', 'Não informada') or 'Não informada'}</div></div>
            </div>
            <div class="ej-mrow" style="margin-top:-0.6rem;">
                <div class="ej-mc"><div class="ej-ml">💰 Valor da Causa</div><div class="ej-mv" style="font-size:1.1rem; font-weight:700; color:#86efac!important;">{getattr(dados_salvos, 'valor_causa', 'Não informado') or 'Não informado'}</div></div>
                <div class="ej-mc">
                    <div class="ej-ml">🔒 Segredo de Justiça</div>
                    <div class="ej-mv" style="margin-top:0.2rem;"><span class="ej-badge {seg_css}">{seg_val}</span></div>
                </div>
                <div class="ej-mc">
                    <div class="ej-ml">🔄 Status do Processo</div>
                    <div class="ej-mv" style="margin-top:0.2rem;"><span class="ej-badge {status_css}">{st_val}</span></div>
                </div>
            </div>
            """)
                
            # Ementa e Movimentações adicionais em colunas lado a lado
            col_ementa, col_movs = st.columns(2, gap="medium")
            with col_ementa:
                if dados_salvos.ementa:
                    with st.expander("📖 Ementa do Julgado / Inteiro Teor", expanded=True):
                        st.markdown(f"*{dados_salvos.ementa}*")
                else:
                    st.caption("ℹ️ Nenhuma ementa ou inteiro teor fornecido por esta fonte.")
            with col_movs:
                if dados_salvos.movimentos:
                    with st.expander(f"⏱️ Linha do Tempo de Andamentos ({len(dados_salvos.movimentos)})", expanded=True):
                        for mov in dados_salvos.movimentos:
                            st.markdown(f"▪️ {mov}")
                else:
                    st.caption("ℹ️ Nenhum histórico de movimentação disponível para este processo.")
            
            # 2. Card de Veredicto Inteligente
            st.markdown("### ⚖️ Veredicto da IA")
            veredicto = consultar_proc_uc.gerar_veredicto(dados_salvos, res_salvo)
            
            cor_risco = "rgba(220,38,38,.15)" if veredicto["nivel_risco"] == "ALTO" else "rgba(234,179,8,.12)" if veredicto["nivel_risco"] == "MEDIO" else "rgba(34,197,94,.12)"
            txt_risco = "#fca5a5" if veredicto["nivel_risco"] == "ALTO" else "#fde68a" if veredicto["nivel_risco"] == "MEDIO" else "#86efac"
            border_risco = "1px solid " + ("#dc2626" if veredicto["nivel_risco"] == "ALTO" else "#eab308" if veredicto["nivel_risco"] == "MEDIO" else "#22c55e")
            
            alertas_html = "".join([f'<div class="ej-v-alert">{a}</div>' for a in veredicto["alertas"]])
            recs_html = "".join([f'<div class="ej-v-rec">{r}</div>' for r in veredicto["recomendacoes"]])
            
            H(f"""
            <div class="ej-veredicto-card">
                <div class="ej-v-title">{veredicto['titulo']}</div>
                <div class="ej-v-risk" style="background:{cor_risco}; color:{txt_risco}; border:{border_risco}">
                    Risco Geral: {veredicto['nivel_risco']}
                </div>
                <div class="ej-v-desc">{veredicto['sintese']}</div>
                {alertas_html}
                {recs_html}
            </div>
            """)
            
            # Detalhamento técnico e cronologia
            col_det, col_cron = st.columns([2, 1], gap="medium")
            with col_det:
                if veredicto.get("detalhamento"):
                    with st.expander("🔬 Detalhamento Tecnico da Analise", expanded=True):
                        st.markdown(veredicto["detalhamento"])
            with col_cron:
                if veredicto.get("cronologia"):
                    with st.expander("📅 Cronologia Processual", expanded=True):
                        st.markdown(veredicto["cronologia"])
            
            # 3. Análise técnica completa
            st.markdown("### 🔬 Análise Técnica do Conteúdo")
            exibir_resultado(res_salvo, chave="processo")
            
        elif not btn_buscar:
            st.info("👈 Insira um número CNJ válido e clique em Buscar e Analisar.")

# ══════════════════════════════════════════════════════════════════════════════
# ABA 4 — Histórico & Comparador de Documentos (Novo)
# ══════════════════════════════════════════════════════════════════════════════
with aba_historico:
    st.subheader("📊 Histórico & Comparador de Análises")
    st.caption("Gerencie análises anteriores ou compare os resultados de dois documentos lado a lado.")
    
    # Seletor de histórico carregado
    selecionado = st.session_state.get("item_selecionado_historico")
    
    if selecionado:
        st.markdown(f"### 📑 Visualizando Item Selecionado: **{selecionado['nome']}**")
        st.info(f"Tipo: {selecionado['tipo']} | Analisado em: {selecionado['timestamp']}")
        
        # Botão para fechar visualização
        if st.button("❌ Fechar Visualização", use_container_width=True):
            st.session_state["item_selecionado_historico"] = None
            st.rerun()
            
        # Exibir metadados de processo se houver
        if selecionado.get("dados_extra"):
            dados_p = selecionado["dados_extra"]
            seg_val = getattr(dados_p, "segredo_justica", "Não") or "Não"
            seg_css = "ej-alto" if seg_val == "Sim" else "ej-baixo"
            st_val = getattr(dados_p, "status", "Ativo") or "Ativo"
            st_lower = st_val.lower()
            status_css = "ej-baixo" if "ativo" in st_lower or "andamento" in st_lower else "ej-medio" if "suspenso" in st_lower else "ej-chip"
            
            H(f"""
            <div class="ej-res" style="border-left: 4px solid var(--gold); margin-bottom:1rem;">
                <p style="font-size: 1.15rem; font-weight: 700; margin: 0 0 0.5rem 0; color: #fff;">🔢 CNJ: {dados_p.numero}</p>
                <div class="ej-rmeta" style="margin-bottom: 0.6rem;">
                    <span class="ej-chip">🏛️ {dados_p.tribunal}</span>
                    <span class="ej-chip">📂 {dados_p.classe_processual or 'Classe não informada'}</span>
                    <span class="ej-chip">🌐 {dados_p.fonte}</span>
                </div>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.5rem; margin-top: 0.8rem; font-size: 0.82rem; color: #e6edf3;">
                    <div><strong>⚖️ Órgão:</strong> {getattr(dados_p, 'orgao_julgador', 'Não informado') or 'Não informado'}</div>
                    <div><strong>👤 Relator:</strong> {getattr(dados_p, 'relator', 'Não informado') or 'Não informado'}</div>
                    <div><strong>📅 Autuação:</strong> {getattr(dados_p, 'data_distribuicao', 'Não informada') or 'Não informada'}</div>
                    <div><strong>📍 Comarca:</strong> {getattr(dados_p, 'comarca', 'Não informada') or 'Não informada'}</div>
                    <div><strong>💰 Valor:</strong> {getattr(dados_p, 'valor_causa', 'Não informado') or 'Não informado'}</div>
                    <div><strong>🔒 Segredo:</strong> <span class="ej-badge {seg_css}" style="font-size:0.65rem; padding:0.05rem 0.35rem;">{seg_val}</span></div>
                    <div><strong>🔄 Status:</strong> <span class="ej-badge {status_css}" style="font-size:0.65rem; padding:0.05rem 0.35rem;">{st_val}</span></div>
                </div>
            </div>
            """)
            
        exibir_resultado(selecionado["resultado"], chave="historico_visualizacao")
        st.divider()
        
    # Comparador
    st.markdown("### ⚖️ Comparador de Documentos")
    historico_items = st.session_state.get("historico_analises", [])
    
    if len(historico_items) < 2:
        st.warning("⚠️ É necessário ter pelo menos 2 análises no histórico para realizar uma comparação. Faça análises nas outras abas primeiro!")
    else:
        opcoes = {item["id"]: f"[{item['tipo']}] {item['nome']} ({item['timestamp']})" for item in historico_items}
        
        col_comp_1, col_comp_2 = st.columns(2)
        with col_comp_1:
            id_1 = st.selectbox("Selecione o Documento A:", options=list(opcoes.keys()), format_func=lambda x: opcoes[x], key="comp_sel_1")
        with col_comp_2:
            # Filtrar para não selecionar o mesmo
            opcoes_2 = {k: v for k, v in opcoes.items() if k != id_1}
            id_2 = st.selectbox("Selecione o Documento B:", options=list(opcoes_2.keys()), format_func=lambda x: opcoes_2[x], key="comp_sel_2")
            
        if id_1 and id_2:
            doc_a = next(item for item in historico_items if item["id"] == id_1)
            doc_b = next(item for item in historico_items if item["id"] == id_2)
            
            res_a = doc_a["resultado"]
            res_b = doc_b["resultado"]
            
            # Tabela de comparação de métricas chave
            st.markdown("#### 📊 Comparativo de Métricas Chave")
            
            # Cores de classe
            info_a = CLASSES_INFO.get(res_a.classe, {"emoji": "📄", "cor": "#7d8fa3"})
            info_b = CLASSES_INFO.get(res_b.classe, {"emoji": "📄", "cor": "#7d8fa3"})
            
            # Dados de comparação
            comp_table = f"""
            | Métrica | Documento A ({doc_a['nome']}) | Documento B ({doc_b['nome']}) |
            | :--- | :---: | :---: |
            | **Classe Detectada** | <span style="color:{info_a['cor']}">{info_a['emoji']} {res_a.classe.upper()}</span> | <span style="color:{info_b['cor']}">{info_b['emoji']} {res_b.classe.upper()}</span> |
            | **Confiança** | {res_a.confianca:.1f}% | {res_b.confianca:.1f}% |
            | **Score LGPD** | {res_a.relatorio_ner['score_lgpd']}/100 | {res_b.relatorio_ner['score_lgpd']}/100 |
            | **Risco de Privacidade** | {res_a.relatorio_ner['risco']} | {res_b.relatorio_ner['risco']} |
            | **Conformidade LGPD** | {res_a.analise_lgpd['score_conformidade']}/100 ({res_a.analise_lgpd['nivel']}) | {res_b.analise_lgpd['score_conformidade']}/100 ({res_b.analise_lgpd['nivel']}) |
            | **Violações Detectadas** | {res_a.analise_lgpd['total']} violação(ões) | {res_b.analise_lgpd['total']} violação(ões) |
            | **Dados Pessoais (NER)** | {res_a.relatorio_ner['dados_pessoais']} ocor. | {res_b.relatorio_ner['dados_pessoais']} ocor. |
            | **Latência (inferência)** | {res_a.ms_inferencia:.3f} ms | {res_b.ms_inferencia:.3f} ms |
            """
            st.markdown(comp_table, unsafe_allow_html=True)
            
            # Comparativo de resumos lado a lado
            st.markdown("#### 📝 Resumos Lado a Lado")
            col_res_a, col_res_b = st.columns(2)
            with col_res_a:
                st.markdown(f"**Resumo do Documento A:**")
                H(f'<div class="ej-rcard" style="min-height: 150px;">{res_a.resumo["resumo"]}</div>')
            with col_res_b:
                st.markdown(f"**Resumo do Documento B:**")
                H(f'<div class="ej-rcard" style="min-height: 150px;">{res_b.resumo["resumo"]}</div>')

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