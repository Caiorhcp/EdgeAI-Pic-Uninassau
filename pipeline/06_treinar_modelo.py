# pipeline/06_treinar_modelo.py — com fixes: NUM_CLASSES dinâmico + batch_size=32
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "2"

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pickle
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

from src.shared.config import (
    X_TRAIN_PATH, X_TEST_PATH, Y_TRAIN_PATH, Y_TEST_PATH,
    ENCODER_PATH, MODEL_KERAS_PATH, MODEL_WEIGHTS_PATH,
    GRAFICO_TREINO_PATH, MODELS_DIR,
    RANDOM_SEED, TRAIN_BATCH_SIZE, TRAIN_EPOCHS,
    EARLY_STOPPING_PATIENCE, EARLY_STOPPING_MONITOR,
)

tf.random.set_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

print("Carregando dados pré-processados…")
X_train = np.load(str(X_TRAIN_PATH))
X_test  = np.load(str(X_TEST_PATH))
y_train = np.load(str(Y_TRAIN_PATH))
y_test  = np.load(str(Y_TEST_PATH))

with open(str(ENCODER_PATH), "rb") as f:
    encoder = pickle.load(f)

# FIX: NUM_CLASSES derivado dinamicamente do encoder (era hardcoded = 5)
NUM_CLASSES = len(encoder.classes_)
N_FEATURES  = X_train.shape[1]
print(f"Features: {N_FEATURES} | Classes: {NUM_CLASSES} → {list(encoder.classes_)}")
print(f"Treino: {X_train.shape[0]} | Teste: {X_test.shape[0]}")

# ─── Arquitetura Dense Neural Network ────────────────────────────────────────
modelo = models.Sequential([
    layers.Input(shape=(N_FEATURES,)),

    layers.Dense(512, activation="relu"),
    layers.BatchNormalization(),
    layers.Dropout(0.4),

    layers.Dense(256, activation="relu"),
    layers.BatchNormalization(),
    layers.Dropout(0.35),

    layers.Dense(128, activation="relu"),
    layers.BatchNormalization(),
    layers.Dropout(0.3),

    layers.Dense(64, activation="relu"),
    layers.Dropout(0.2),

    layers.Dense(NUM_CLASSES, activation="softmax"),
], name="juridico_dnn")

modelo.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)
modelo.summary()

# ─── Callbacks ────────────────────────────────────────────────────────────────
cb_early = callbacks.EarlyStopping(
    monitor=EARLY_STOPPING_MONITOR,
    patience=EARLY_STOPPING_PATIENCE,
    restore_best_weights=True,
    verbose=1,
)
os.makedirs(str(MODELS_DIR), exist_ok=True)
cb_ckpt = callbacks.ModelCheckpoint(
    str(MODEL_WEIGHTS_PATH),
    monitor=EARLY_STOPPING_MONITOR,
    save_best_only=True, save_weights_only=True, verbose=0,
)
cb_reduce_lr = callbacks.ReduceLROnPlateau(
    monitor="val_loss", factor=0.5, patience=8, min_lr=1e-6, verbose=1,
)

print(f"\nTreinando {TRAIN_EPOCHS} épocas (batch_size={TRAIN_BATCH_SIZE})…")
hist = modelo.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=TRAIN_EPOCHS,
    batch_size=TRAIN_BATCH_SIZE,   # FIX: era 8, agora 32
    callbacks=[cb_early, cb_ckpt, cb_reduce_lr],
    verbose=1,
)

# ─── Avaliação ────────────────────────────────────────────────────────────────
loss, acc = modelo.evaluate(X_test, y_test, verbose=0)
print(f"\nAcurácia no teste: {acc*100:.2f}%")

# ─── Salvar modelo ────────────────────────────────────────────────────────────
modelo.save(str(MODEL_KERAS_PATH))
print(f"Modelo salvo: {MODEL_KERAS_PATH}")

# ─── Gráfico de treino ────────────────────────────────────────────────────────
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(hist.history["accuracy"],     label="treino")
axes[0].plot(hist.history["val_accuracy"], label="validação")
axes[0].set_title("Acurácia"); axes[0].legend(); axes[0].grid(True)
axes[1].plot(hist.history["loss"],     label="treino")
axes[1].plot(hist.history["val_loss"], label="validação")
axes[1].set_title("Loss"); axes[1].legend(); axes[1].grid(True)
plt.tight_layout()
plt.savefig(str(GRAFICO_TREINO_PATH), dpi=120)
plt.close()
print(f"Gráfico salvo: {GRAFICO_TREINO_PATH}")
