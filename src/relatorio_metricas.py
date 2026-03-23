# src/relatorio_metricas.py
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import re, pickle, time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import tensorflow as tf
from sklearn.metrics import (
    classification_report, confusion_matrix, ConfusionMatrixDisplay
)

# ─── Carregar artefatos ───────────────────────────────────────────────────────
modelo    = tf.keras.models.load_model("models/modelo_juridico.keras")
interp    = tf.lite.Interpreter("models/tflite/modelo_juridico_int8.tflite")
interp.allocate_tensors()
inp  = interp.get_input_details()
out  = interp.get_output_details()

with open("data/processed/vectorizer.pkl", "rb") as f: vectorizer = pickle.load(f)
with open("data/processed/encoder.pkl",    "rb") as f: encoder    = pickle.load(f)

X_test  = np.load("data/processed/X_test.npy").astype(np.float32)
y_test  = np.load("data/processed/y_test.npy")
X_train = np.load("data/processed/X_train.npy").astype(np.float32)
y_train = np.load("data/processed/y_train.npy")

CLASSES = list(encoder.classes_)
os.makedirs("models/relatorio", exist_ok=True)

# ─── 1. Métricas Keras vs TFLite ─────────────────────────────────────────────
_, acc_keras = modelo.evaluate(X_test, y_test, verbose=0)
y_pred_keras = np.argmax(modelo.predict(X_test, verbose=0), axis=1)

def pred_tflite(X):
    preds = []
    for i in range(len(X)):
        interp.set_tensor(inp[0]['index'], X[i:i+1])
        interp.invoke()
        preds.append(interp.get_tensor(out[0]['index'])[0])
    return np.array(preds)

y_pred_tflite = np.argmax(pred_tflite(X_test), axis=1)
acc_tflite    = np.mean(y_pred_tflite == y_test)

print("=" * 55)
print("RELATÓRIO DE MÉTRICAS — Edge AI Jurídico")
print("=" * 55)

print(f"\n1. ACURÁCIA GERAL")
print(f"   Keras  (float32): {acc_keras  * 100:.1f}%")
print(f"   TFLite (INT8)   : {acc_tflite * 100:.1f}%")
print(f"   Degradação      : {(acc_keras - acc_tflite) * 100:.1f} pp")

# ─── 2. Relatório por classe ─────────────────────────────────────────────────
print(f"\n2. DESEMPENHO POR CLASSE (TFLite INT8)")
print(classification_report(y_test, y_pred_tflite, target_names=CLASSES))

# ─── 3. Benchmark de tamanho ─────────────────────────────────────────────────
tam_keras  = os.path.getsize("models/modelo_juridico.keras")          / 1024
tam_tflite = os.path.getsize("models/tflite/modelo_juridico.tflite")  / 1024
tam_int8   = os.path.getsize("models/tflite/modelo_juridico_int8.tflite") / 1024

print(f"3. TAMANHO DOS MODELOS")
print(f"   Keras  (treino) : {tam_keras:>8.1f} KB  (referência)")
print(f"   TFLite (base)   : {tam_tflite:>8.1f} KB  ({(1-tam_tflite/tam_keras)*100:.0f}% redução)")
print(f"   TFLite (INT8)   : {tam_int8:>8.1f} KB  ({(1-tam_int8/tam_keras)*100:.0f}% redução)")

# ─── 4. Benchmark de velocidade ──────────────────────────────────────────────
v = X_test[0:1]

N = 500
t0 = time.time()
for _ in range(N):
    modelo.predict(v, verbose=0)
ms_keras = (time.time() - t0) / N * 1000

t0 = time.time()
for _ in range(N):
    interp.set_tensor(inp[0]['index'], v)
    interp.invoke()
    interp.get_tensor(out[0]['index'])
ms_tflite = (time.time() - t0) / N * 1000

print(f"\n4. VELOCIDADE DE INFERÊNCIA ({N} amostras)")
print(f"   Keras  : {ms_keras:.3f} ms/inferência")
print(f"   TFLite : {ms_tflite:.3f} ms/inferência")
print(f"   Speedup: {ms_keras/ms_tflite:.1f}x mais rápido")

# ─── 5. Gráficos ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 10))
fig.suptitle("Edge AI Jurídico — Relatório de Métricas\nClassificação de Documentos + LGPD",
             fontsize=14, fontweight="bold")

# 5.1 Matriz de confusão
ax1 = fig.add_subplot(2, 3, 1)
cm  = confusion_matrix(y_test, y_pred_tflite)
disp = ConfusionMatrixDisplay(cm, display_labels=CLASSES)
disp.plot(ax=ax1, colorbar=False, cmap="Blues")
ax1.set_title("Matriz de Confusão\n(TFLite INT8)", fontsize=11)
ax1.tick_params(axis='x', rotation=30)

# 5.2 Comparação de tamanho
ax2 = fig.add_subplot(2, 3, 2)
nomes  = ["Keras\n(float32)", "TFLite\n(base)", "TFLite\n(INT8)"]
tamanhos = [tam_keras, tam_tflite, tam_int8]
cores  = ["#e74c3c", "#f39c12", "#27ae60"]
bars   = ax2.bar(nomes, tamanhos, color=cores, edgecolor="white", width=0.5)
for bar, val in zip(bars, tamanhos):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
             f"{val:.0f} KB", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax2.set_title("Tamanho dos Modelos (KB)", fontsize=11)
ax2.set_ylabel("KB")
ax2.grid(axis="y", alpha=0.3)

# 5.3 Comparação de velocidade
ax3 = fig.add_subplot(2, 3, 3)
v_nomes  = ["Keras", "TFLite INT8"]
v_tempos = [ms_keras, ms_tflite]
v_cores  = ["#e74c3c", "#27ae60"]
bars3    = ax3.bar(v_nomes, v_tempos, color=v_cores, edgecolor="white", width=0.4)
for bar, val in zip(bars3, v_tempos):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
             f"{val:.3f} ms", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax3.set_title("Latência por Inferência (ms)", fontsize=11)
ax3.set_ylabel("ms")
ax3.grid(axis="y", alpha=0.3)

# 5.4 F1-score por classe
ax4 = fig.add_subplot(2, 3, 4)
from sklearn.metrics import f1_score
f1s  = f1_score(y_test, y_pred_tflite, average=None)  # pyright: ignore
bars4 = ax4.barh(CLASSES, f1s, color="#3498db", edgecolor="white")
for bar, val in zip(bars4, f1s):  # pyright: ignore
    ax4.text(val + 0.01, bar.get_y() + bar.get_height()/2,
             f"{val:.2f}", va="center", fontsize=10)
ax4.set_xlim(0, 1.15)
ax4.set_title("F1-Score por Classe", fontsize=11)
ax4.axvline(x=0.7, color="orange", linestyle="--", alpha=0.7, label="Meta 0.7")
ax4.legend(fontsize=9)
ax4.grid(axis="x", alpha=0.3)

# 5.5 Redução de tamanho acumulada
ax5 = fig.add_subplot(2, 3, 5)
etapas    = ["Keras\noriginal", "→ TFLite\nbase", "→ TFLite\nINT8"]
reducoes  = [100, tam_tflite/tam_keras*100, tam_int8/tam_keras*100]
ax5.plot(etapas, reducoes, "o-", color="#8e44ad", linewidth=2.5, markersize=10)
for i, (e, r) in enumerate(zip(etapas, reducoes)):
    ax5.annotate(f"{r:.1f}%", (e, r),  # pyright: ignore
                 textcoords="offset points", xytext=(0, 12),
                 ha="center", fontsize=10, fontweight="bold")
ax5.set_ylim(0, 120)
ax5.set_title("Tamanho Relativo ao Keras (%)", fontsize=11)
ax5.set_ylabel("% do tamanho original")
ax5.grid(alpha=0.3)
ax5.fill_between(range(len(etapas)), reducoes, alpha=0.1, color="#8e44ad")

# 5.6 Tabela resumo
ax6 = fig.add_subplot(2, 3, 6)
ax6.axis("off")
dados_tabela = [
    ["Métrica",          "Valor"],
    ["Acurácia Keras",   f"{acc_keras*100:.1f}%"],
    ["Acurácia TFLite",  f"{acc_tflite*100:.1f}%"],
    ["Tamanho Keras",    f"{tam_keras:.0f} KB"],
    ["Tamanho TFLite",   f"{tam_int8:.0f} KB"],
    ["Redução tamanho",  f"{(1-tam_int8/tam_keras)*100:.0f}%"],
    ["Latência TFLite",  f"{ms_tflite:.3f} ms"],
    ["Throughput",       f"{1000/ms_tflite:.0f} inf/s"],
    ["Técnica",          "TF-IDF + Dense"],
    ["Otimização",       "Quantização INT8"],
]
tabela = ax6.table(
    cellText=dados_tabela[1:],
    colLabels=dados_tabela[0],
    cellLoc="center", loc="center",
    colWidths=[0.55, 0.4]
)
tabela.auto_set_font_size(False)
tabela.set_fontsize(10)
tabela.scale(1, 1.5)
for (r, c), cell in tabela.get_celld().items():
    if r == 0:
        cell.set_facecolor("#2c3e50")
        cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#ecf0f1")
ax6.set_title("Resumo Executivo", fontsize=11)

plt.tight_layout()
caminho_fig = "models/relatorio/relatorio_metricas.png"
plt.savefig(caminho_fig, dpi=150, bbox_inches="tight")
print(f"\n5. Gráfico salvo em {caminho_fig}")
print("\n" + "=" * 55)
print("Relatório concluído!")