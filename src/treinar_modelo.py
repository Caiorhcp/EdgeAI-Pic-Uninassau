# src/treinar_modelo.py — versão melhorada: TF-IDF 8k + trigramas + Dense(512) + Label Smoothing
import os
import ctypes
# Remove TF_USE_LEGACY_KERAS do ambiente C/C++ do Windows para evitar conflitos na lazy initialization
if "TF_USE_LEGACY_KERAS" in os.environ:
    del os.environ["TF_USE_LEGACY_KERAS"]
try:
    ctypes.windll.kernel32.SetEnvironmentVariableW("TF_USE_LEGACY_KERAS", None)
except Exception:
    pass

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import re, pickle
import numpy as np
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
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report

print("=" * 60)
print("Edge AI Juridico - Treinamento v3.0 (Metricas Otimizadas)")
print("  TF-IDF: 5k features + bigramas")
print("  Arquitetura: Dense(128->64) + L2 Regularization + Dropout(0.5/0.4)")
print("  Balanceamento: Random Oversampling Físico no Treino (Zero Leakage)")
print("  ReduceLROnPlateau: fator 0.5, patience 10")
print("=" * 60)

print("\nCarregando dados...")
X_train = np.load("data/processed/X_train.npy")
X_test  = np.load("data/processed/X_test.npy")
y_train = np.load("data/processed/y_train.npy")
y_test  = np.load("data/processed/y_test.npy")

with open("data/processed/encoder.pkl",    "rb") as f: encoder    = pickle.load(f)
with open("data/processed/vectorizer.pkl", "rb") as f: vectorizer = pickle.load(f)

print(f"Treino bruto: {X_train.shape} | Teste: {X_test.shape}")
print(f"Classes: {list(encoder.classes_)}")

# Split de validação manual antes de qualquer balanceamento para evitar data leakage
from sklearn.model_selection import train_test_split
X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
    X_train, y_train, test_size=0.15, stratify=y_train, random_state=42
)

# Random Oversampling Físico no split de treino usando Numpy + Jittering (ruído nos não-zeros)
classes_unicas, contagens = np.unique(y_train_split, return_counts=True)
max_samples = np.max(contagens)
print(f"\nAmostras por classe no treino antes do oversampling: {dict(zip(classes_unicas, contagens))}")
print(f"Objetivo de balanceamento: {max_samples} amostras por classe")

X_train_resampled = []
y_train_resampled = []

for cl, count in zip(classes_unicas, contagens):
    idx_classe = np.where(y_train_split == cl)[0]
    X_classe = X_train_split[idx_classe]
    y_classe = y_train_split[idx_classe]
    
    if count < max_samples:
        # Fazer oversampling por amostragem aleatória com reposição
        num_faltando = max_samples - count
        indices_aleatorios = np.random.choice(idx_classe, size=num_faltando, replace=True)
        X_duplicados = X_train_split[indices_aleatorios].copy()
        
        # Adicionar ruído sutil apenas nos elementos não-zero para preservar a estrutura de esparsidade e evitar memorização (overfitting)
        np.random.seed(42 + cl)
        non_zeros = X_duplicados > 0
        ruido = np.random.normal(0, 0.01, size=X_duplicados.shape)
        X_duplicados[non_zeros] = np.clip(X_duplicados[non_zeros] + ruido[non_zeros], 0.01, 1.0)
        
        X_resampled_classe = np.concatenate([X_classe, X_duplicados], axis=0)
        y_resampled_classe = np.concatenate([y_classe, y_train_split[indices_aleatorios]], axis=0)
    else:
        X_resampled_classe = X_classe
        y_resampled_classe = y_classe
        
    X_train_resampled.append(X_resampled_classe)
    y_train_resampled.append(y_resampled_classe)

X_train_resampled = np.concatenate(X_train_resampled, axis=0)
y_train_resampled = np.concatenate(y_train_resampled, axis=0)

# Embaralhar para o treinamento não ficar enviesado pela ordem das classes
np.random.seed(42)
indices_misturados = np.random.permutation(len(y_train_resampled))
X_train_resampled = X_train_resampled[indices_misturados]
y_train_resampled = y_train_resampled[indices_misturados]

print(f"Treino após oversampling + noise: {X_train_resampled.shape}")
print(f"Validação (sem oversampling): {X_val_split.shape}")

INPUT_DIM   = X_train_resampled.shape[1]
NUM_CLASSES = len(encoder.classes_)

# ─── Arquitetura Compacta e Altamente Regularizada ───────────────────────────
# 64 → 32 → NUM_CLASSES com L2 regularization (5e-4) e Dropout robusto
# ─────────────────────────────────────────────────────────────────────────────
modelo = Sequential([
    tf.keras.Input(shape=(INPUT_DIM,)),
    # Camada 1
    Dense(64, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(5e-4)),
    BatchNormalization(),
    Dropout(0.4),
    # Camada 2
    Dense(32, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(5e-4)),
    BatchNormalization(),
    Dropout(0.3),
    # Saída
    Dense(NUM_CLASSES, activation="softmax"),
], name="edge_ai_juridico_regularized")

modelo.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(
        from_logits=False,
        name="sparse_categorical_crossentropy"
    ),
    metrics=["accuracy"],
)

modelo.summary()
os.makedirs("models", exist_ok=True)

# ─── Callbacks ────────────────────────────────────────────────────────────────
early_stop = EarlyStopping(
    monitor="val_accuracy", patience=40,
    restore_best_weights=True, verbose=1,
)
checkpoint = ModelCheckpoint(
    "models/modelo_juridico.keras",
    monitor="val_accuracy", save_best_only=True, verbose=1,
)
reduce_lr = ReduceLROnPlateau(
    monitor="val_loss", factor=0.5, patience=12,
    min_lr=1e-6, verbose=1,
)

# ─── Treinamento ──────────────────────────────────────────────────────────────
print("\nTreinando...")
hist = modelo.fit(
    X_train_resampled, y_train_resampled,
    epochs=200,
    batch_size=16,
    validation_data=(X_val_split, y_val_split),
    callbacks=[early_stop, checkpoint, reduce_lr],
    verbose=1,
)

# ─── Avaliação ────────────────────────────────────────────────────────────────
loss, acc = modelo.evaluate(X_test, y_test, verbose=0)
print(f"\n{'='*60}")
print(f"Avaliação no conjunto de teste:")
print(f"  Loss    : {loss:.4f}")
print(f"  Accuracy: {acc * 100:.2f}%")

y_pred = np.argmax(modelo.predict(X_test, verbose=0), axis=1)
print("\nRelatório por classe:")
report = classification_report(y_test, y_pred, target_names=encoder.classes_, digits=4)
print(report)

# Extrair F1 médio para log
from sklearn.metrics import f1_score
f1_macro = f1_score(y_test, y_pred, average="macro")
f1_weighted = f1_score(y_test, y_pred, average="weighted")
print(f"  F1 Macro   : {f1_macro:.4f}")
print(f"  F1 Weighted: {f1_weighted:.4f}")
print(f"  Meta F1    : >= 0.93")
print(f"  Status     : {'[OK] META ATINGIDA' if f1_macro >= 0.93 else '[AVISO] Treinar com mais dados'}")
print("=" * 60)

# ─── Teste Manual ─────────────────────────────────────────────────────────────
def classificar(texto: str):
    t = re.sub(r"[^a-záàãâéêíóôõúüç\s]", " ", texto.lower())
    v = vectorizer.transform([t]).toarray()
    p = modelo.predict(v, verbose=0)
    i = np.argmax(p)
    return encoder.classes_[i], p[0][i] * 100

print("\nTeste manual:")
exemplos = [
    "O titular tem direito à exclusão de seus dados pessoais conforme LGPD.",
    "Acórdão: por unanimidade, negado provimento ao recurso especial.",
    "Cláusula segunda: o pagamento será feito até o décimo dia do mês.",
    "Excelentíssimo Senhor Juiz, vem o requerente propor a presente ação.",
    "O princípio da legalidade é fundamento do Estado Democrático de Direito.",
    "O controlador de dados deve adotar medidas técnicas de segurança.",
    "O agravo regimental não merece provimento ante a ausência de argumentos novos.",
]
for t in exemplos:
    c, conf = classificar(t)
    marker = "[OK]" if conf >= 80 else "[AVISO]"
    print(f"  {marker} [{c.upper():10s}] {conf:5.1f}%  ->  {t[:65]}...")

# ─── Gráficos ─────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
fig.suptitle("Edge AI Jurídico v2.0 — Treinamento", fontsize=13, fontweight="bold")

# Acurácia
ax1 = axes[0]
ax1.plot(hist.history["accuracy"],     label="Treino", color="#3498db", linewidth=2)
ax1.plot(hist.history["val_accuracy"], label="Validação", color="#e74c3c", linewidth=2)
ax1.axhline(y=0.93, color="#27ae60", linestyle="--", alpha=0.7, label="Meta 93%")
ax1.set_title("Acurácia"); ax1.legend(); ax1.grid(alpha=0.3)
ax1.set_xlabel("Época"); ax1.set_ylabel("Acurácia")

# Loss
ax2 = axes[1]
ax2.plot(hist.history["loss"],     label="Treino", color="#3498db", linewidth=2)
ax2.plot(hist.history["val_loss"], label="Validação", color="#e74c3c", linewidth=2)
ax2.set_title("Loss"); ax2.legend(); ax2.grid(alpha=0.3)
ax2.set_xlabel("Época"); ax2.set_ylabel("Loss")

# Learning rate (se disponível)
ax3 = axes[2]
if "lr" in hist.history:
    ax3.plot(hist.history["lr"], color="#8e44ad", linewidth=2)
    ax3.set_title("Learning Rate")
    ax3.set_xlabel("Época"); ax3.set_ylabel("LR")
    ax3.grid(alpha=0.3)
else:
    ax3.axis("off")
    ax3.text(0.5, 0.5, f"Acurácia Final\n{acc*100:.2f}%\n\nF1 Macro\n{f1_macro:.4f}",
             ha="center", va="center", fontsize=16, fontweight="bold",
             transform=ax3.transAxes)

plt.tight_layout()
plt.savefig("models/grafico_treinamento.png", dpi=150)
print("\nGráfico salvo em models/grafico_treinamento.png")

# ─── Salvar pesos ─────────────────────────────────────────────────────────────
modelo.save_weights("models/modelo_juridico.weights.h5")
print("Pesos salvos em models/modelo_juridico.weights.h5")

# ─── Salvar métricas para a UI ────────────────────────────────────────────────
import json
metricas = {
    "acuracia_keras": float(acc),
    "f1_macro": float(f1_macro),
    "f1_weighted": float(f1_weighted),
    "n_treino": int(len(X_train)),
    "n_teste": int(len(X_test)),
    "input_dim": int(INPUT_DIM),
    "num_classes": int(NUM_CLASSES),
    "classes": list(encoder.classes_),
    "epocas_treinadas": len(hist.history["accuracy"]),
}
os.makedirs("models/relatorio", exist_ok=True)
with open("models/relatorio/metricas.json", "w", encoding="utf-8") as f:
    json.dump(metricas, f, ensure_ascii=False, indent=2)
print("Métricas salvas em models/relatorio/metricas.json")
print("\n[OK] Treinamento concluido! Proximo passo: python src/converter_tflite.py")