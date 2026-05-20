# src/validacao_kfold.py
# Validação cruzada k-fold estratificada
# Substitui o split 80/20 simples por 10 avaliações rotativas
# Resultado: métricas com média e desvio padrão — muito mais confiáveis para publicação

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "2"

import numpy as np
import pickle
import json
import matplotlib.pyplot as plt
plt.style.use('ggplot')
plt.rcParams.update({
    "figure.facecolor": "#fcfcfc",
    "axes.facecolor": "#ffffff",
    "axes.edgecolor": "#e0e0e0",
    "axes.grid": True,
    "grid.color": "#f0f0f0",
    "text.color": "#333333",
    "xtick.color": "#555555",
    "ytick.color": "#555555",
    "font.family": "sans-serif",
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
})
import tensorflow as tf
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score
)

# ─── Carregar dados COMPLETOS (sem split prévio) ──────────────────────────────
print("Carregando dados completos para k-fold...")
X_train = np.load("data/processed/X_train.npy").astype(np.float32)
X_test  = np.load("data/processed/X_test.npy").astype(np.float32)
y_train = np.load("data/processed/y_train.npy")
y_test  = np.load("data/processed/y_test.npy")

# Unir treino e teste — o k-fold vai fazer as divisões por conta própria
X_completo = np.vstack([X_train, X_test])
y_completo = np.concatenate([y_train, y_test])

with open("data/processed/encoder.pkl", "rb") as f:
    encoder = pickle.load(f)

CLASSES   = list(encoder.classes_)
N_SPLITS  = 10
INPUT_DIM = X_completo.shape[1]

print(f"Total de amostras: {len(X_completo)}")
print(f"Features (TF-IDF): {INPUT_DIM}")
print(f"Folds: {N_SPLITS}")
print(f"Amostras por fold (aprox.): {len(X_completo) // N_SPLITS}")

# ─── Função para construir o modelo ──────────────────────────────────────────
def construir_modelo():
    m = tf.keras.Sequential([
        tf.keras.Input(shape=(INPUT_DIM,)),
        tf.keras.layers.Dense(256, activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(len(CLASSES), activation="softmax"),
    ])
    m.compile(
        optimizer=tf.keras.optimizers.Adam(0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return m

# ─── K-Fold estratificado ─────────────────────────────────────────────────────
# StratifiedKFold garante que cada fold tenha a mesma proporção de classes
# Isso é essencial para datasets desbalanceados como o nosso

skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)

metricas_folds = []

print("\n" + "="*60)
print(f"VALIDAÇÃO CRUZADA ESTRATIFICADA — {N_SPLITS} FOLDS")
print("="*60)

for fold, (idx_treino, idx_val) in enumerate(skf.split(X_completo, y_completo)):
    print(f"\nFold {fold+1}/{N_SPLITS}...")

    X_fold_treino = X_completo[idx_treino]
    y_fold_treino = y_completo[idx_treino]
    X_fold_val    = X_completo[idx_val]
    y_fold_val    = y_completo[idx_val]

    # Construir modelo limpo a cada fold
    modelo = construir_modelo()

    # Treinar
    modelo.fit(
        X_fold_treino, y_fold_treino,
        epochs=150,
        batch_size=16,
        validation_data=(X_fold_val, y_fold_val),
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=20,
                restore_best_weights=True,
                verbose=0
            )
        ],
        verbose=0
    )

    # Avaliar
    y_pred = np.argmax(modelo.predict(X_fold_val, verbose=0), axis=1)

    acc       = accuracy_score(y_fold_val, y_pred)
    f1_macro  = f1_score(y_fold_val, y_pred, average="macro",    zero_division=0)  # pyright: ignore
    f1_weight = f1_score(y_fold_val, y_pred, average="weighted", zero_division=0)  # pyright: ignore
    prec      = precision_score(y_fold_val, y_pred, average="macro", zero_division=0)  # pyright: ignore
    rec       = recall_score(y_fold_val, y_pred, average="macro",    zero_division=0)  # pyright: ignore

    # F1 por classe
    f1_classes = f1_score(y_fold_val, y_pred, average=None, zero_division=0)  # pyright: ignore

    fold_resultado = {
        "fold":       fold + 1,
        "acc":        acc,
        "f1_macro":   f1_macro,
        "f1_weight":  f1_weight,
        "precision":  prec,
        "recall":     rec,
        "f1_classes": {CLASSES[i]: float(f1_classes[i]) for i in range(len(CLASSES))},  # type: ignore[index]
        "n_treino":   len(idx_treino),
        "n_val":      len(idx_val),
    }
    metricas_folds.append(fold_resultado)

    print(f"  Acurácia : {acc*100:.1f}%")
    print(f"  F1 macro : {f1_macro:.3f}")
    print(f"  F1 weight: {f1_weight:.3f}")

    # Liberar memória entre folds
    del modelo
    tf.keras.backend.clear_session()

# ─── Calcular estatísticas finais ─────────────────────────────────────────────
accs      = [r["acc"]       for r in metricas_folds]
f1_macros = [r["f1_macro"]  for r in metricas_folds]
f1_weights= [r["f1_weight"] for r in metricas_folds]
precs     = [r["precision"] for r in metricas_folds]
recs      = [r["recall"]    for r in metricas_folds]

# F1 por classe
f1_por_classe = {cls: [] for cls in CLASSES}
for r in metricas_folds:
    for cls in CLASSES:
        f1_por_classe[cls].append(r["f1_classes"][cls])

print("\n" + "="*60)
print("RESULTADOS FINAIS — VALIDAÇÃO CRUZADA K-FOLD")
print("="*60)

print(f"\nAcurácia   : {np.mean(accs)*100:.2f}% ± {np.std(accs)*100:.2f}%")
print(f"F1 macro   : {np.mean(f1_macros):.4f} ± {np.std(f1_macros):.4f}")
print(f"F1 weight  : {np.mean(f1_weights):.4f} ± {np.std(f1_weights):.4f}")
print(f"Precisão   : {np.mean(precs):.4f} ± {np.std(precs):.4f}")
print(f"Recall     : {np.mean(recs):.4f} ± {np.std(recs):.4f}")

print(f"\nF1-score por classe (média ± desvio):")
for cls in CLASSES:
    vals = f1_por_classe[cls]
    print(f"  {cls:10s}: {np.mean(vals):.4f} ± {np.std(vals):.4f}")

# Intervalo de confiança 95% (t-distribution aproximada)
import math
n = N_SPLITS
t95 = 2.262  # t-crítico para 9 graus de liberdade, 95% confiança

ic_acc = t95 * (np.std(accs) / math.sqrt(n))
print(f"\nIntervalo de confiança 95% para acurácia:")
print(f"  {np.mean(accs)*100:.2f}% ± {ic_acc*100:.2f}%")
print(f"  [{(np.mean(accs)-ic_acc)*100:.2f}%, {(np.mean(accs)+ic_acc)*100:.2f}%]")

# ─── Gráficos ─────────────────────────────────────────────────────────────────
os.makedirs("models/relatorio", exist_ok=True)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(f"Validação Cruzada {N_SPLITS}-Fold — Edge AI Jurídico",
             fontsize=14, fontweight="bold")

folds_x = [r["fold"] for r in metricas_folds]

# 1. Acurácia por fold
ax1 = axes[0, 0]
ax1.plot(folds_x, [a*100 for a in accs], "o-", color="#2980b9",
         linewidth=2, markersize=8, label="Acurácia por fold")
ax1.axhline(np.mean(accs)*100, color="#e74c3c", linestyle="--",
            linewidth=1.5, label=f"Média: {np.mean(accs)*100:.2f}%")
ax1.fill_between(folds_x,
    [(np.mean(accs)-np.std(accs))*100]*N_SPLITS,
    [(np.mean(accs)+np.std(accs))*100]*N_SPLITS,
    alpha=0.15, color="#2980b9", label=f"±1σ ({np.std(accs)*100:.2f}%)")
ax1.set_title("Acurácia por fold (%)")
ax1.set_xlabel("Fold")
ax1.set_ylabel("Acurácia (%)")
ax1.set_xticks(folds_x)
ax1.legend(fontsize=9)
ax1.grid(alpha=0.3)
ax1.set_ylim(70, 100)

# 2. F1 macro por fold
ax2 = axes[0, 1]
ax2.plot(folds_x, f1_macros, "o-", color="#27ae60",
         linewidth=2, markersize=8, label="F1 macro")
ax2.plot(folds_x, f1_weights, "s--", color="#8e44ad",
         linewidth=1.5, markersize=6, label="F1 weighted")
ax2.axhline(np.mean(f1_macros), color="#27ae60", linestyle=":",
            alpha=0.7, label=f"Média macro: {np.mean(f1_macros):.4f}")
ax2.set_title("F1-Score por fold")
ax2.set_xlabel("Fold")
ax2.set_ylabel("F1-Score")
ax2.set_xticks(folds_x)
ax2.legend(fontsize=9)
ax2.grid(alpha=0.3)
ax2.set_ylim(0.7, 1.0)

# 3. F1 por classe (boxplot)
ax3 = axes[1, 0]
dados_box  = [f1_por_classe[cls] for cls in CLASSES]
bp = ax3.boxplot(dados_box, labels=CLASSES, patch_artist=True,
                 medianprops=dict(color="black", linewidth=2))
cores_box = ["#8e44ad", "#2980b9", "#27ae60", "#7f8c8d", "#e67e22"]
for patch, cor in zip(bp["boxes"], cores_box):
    patch.set_facecolor(cor)
    patch.set_alpha(0.7)
ax3.set_title("Distribuição F1-Score por classe (10 folds)")
ax3.set_ylabel("F1-Score")
ax3.axhline(0.8, color="gray", linestyle="--", alpha=0.5, label="Meta 0.8")
ax3.legend(fontsize=9)
ax3.grid(axis="y", alpha=0.3)

# 4. Tabela resumo
ax4 = axes[1, 1]
ax4.axis("off")
dados_tabela = [
    ["Métrica", "Média", "Desvio", "IC 95%"],
    ["Acurácia",  f"{np.mean(accs)*100:.2f}%",
                  f"±{np.std(accs)*100:.2f}%",
                  f"[{(np.mean(accs)-ic_acc)*100:.1f}%, {(np.mean(accs)+ic_acc)*100:.1f}%]"],
    ["F1 macro",  f"{np.mean(f1_macros):.4f}",
                  f"±{np.std(f1_macros):.4f}", "—"],
    ["F1 weight", f"{np.mean(f1_weights):.4f}",
                  f"±{np.std(f1_weights):.4f}", "—"],
    ["Precisão",  f"{np.mean(precs):.4f}",
                  f"±{np.std(precs):.4f}", "—"],
    ["Recall",    f"{np.mean(recs):.4f}",
                  f"±{np.std(recs):.4f}", "—"],
    ["Folds",     str(N_SPLITS), "—", "—"],
    ["Amostras",  str(len(X_completo)), "—", "—"],
]
tabela = ax4.table(
    cellText=dados_tabela[1:],
    colLabels=dados_tabela[0],
    cellLoc="center", loc="center",
    colWidths=[0.28, 0.22, 0.22, 0.28]
)
tabela.auto_set_font_size(False)
tabela.set_fontsize(9)
tabela.scale(1, 1.6)
for (r, c), cell in tabela.get_celld().items():
    if r == 0:
        cell.set_facecolor("#1a1a2e")
        cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#f0f8ff")
ax4.set_title("Resumo estatístico — 10-Fold CV", fontsize=11)

plt.tight_layout()
caminho_fig = "models/relatorio/kfold_resultados.png"
plt.savefig(caminho_fig, dpi=150, bbox_inches="tight")
print(f"\nGráfico salvo em {caminho_fig}")

# ─── Salvar JSON para o artigo ────────────────────────────────────────────────
resumo_json = {
    "configuracao": {
        "n_folds":    N_SPLITS,
        "n_amostras": len(X_completo),
        "estrategia": "StratifiedKFold",
        "random_state": 42,
    },
    "resultados": {
        "acuracia": {
            "media":   round(np.mean(accs) * 100, 2),
            "desvio":  round(np.std(accs) * 100, 2),
            "ic95_lower": round((np.mean(accs) - ic_acc) * 100, 2),
            "ic95_upper": round((np.mean(accs) + ic_acc) * 100, 2),
        },
        "f1_macro": {
            "media":  round(np.mean(f1_macros), 4),
            "desvio": round(np.std(f1_macros), 4),
        },
        "f1_por_classe": {
            cls: {
                "media":  round(np.mean(f1_por_classe[cls]), 4),
                "desvio": round(np.std(f1_por_classe[cls]), 4),
            }
            for cls in CLASSES
        },
    },
    "folds": metricas_folds,
}

caminho_json = "models/relatorio/kfold_resultados.json"
with open(caminho_json, "w", encoding="utf-8") as f:
    json.dump(resumo_json, f, ensure_ascii=False, indent=2)

print(f"JSON salvo em {caminho_json}")
print("\n" + "="*60)
print("TEXTO PRONTO PARA O ARTIGO")
print("="*60)
print(
    f"A validação cruzada estratificada com {N_SPLITS} folds resultou em "
    f"acurácia média de {np.mean(accs)*100:.2f}% ± {np.std(accs)*100:.2f}% "
    f"(IC 95%: [{(np.mean(accs)-ic_acc)*100:.1f}%, "
    f"{(np.mean(accs)+ic_acc)*100:.1f}%]), "
    f"F1-score macro de {np.mean(f1_macros):.4f} ± {np.std(f1_macros):.4f} "
    f"e F1-score ponderado de {np.mean(f1_weights):.4f} ± {np.std(f1_weights):.4f}."
)