# src/treinar_modelo.py — versão TF-IDF + rede densa
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
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.utils.class_weight import compute_class_weight

print("Carregando dados...")
X_train = np.load("data/processed/X_train.npy")
X_test  = np.load("data/processed/X_test.npy")
y_train = np.load("data/processed/y_train.npy")
y_test  = np.load("data/processed/y_test.npy")

with open("data/processed/encoder.pkl",    "rb") as f: encoder    = pickle.load(f)
with open("data/processed/vectorizer.pkl", "rb") as f: vectorizer = pickle.load(f)

print(f"Treino: {X_train.shape} | Teste: {X_test.shape}")

INPUT_DIM   = X_train.shape[1]
NUM_CLASSES = 5

modelo = Sequential([
    tf.keras.Input(shape=(INPUT_DIM,)),
    Dense(64, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(0.001)),
    BatchNormalization(),
    Dropout(0.3),
    Dense(32, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(0.001)),
    Dropout(0.2),
    Dense(NUM_CLASSES, activation="softmax")
])

modelo.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

modelo.summary()
os.makedirs("models", exist_ok=True)

early_stop = EarlyStopping(
    monitor="val_accuracy", patience=20,
    restore_best_weights=True, verbose=1
)
checkpoint = ModelCheckpoint(
    "models/modelo_juridico.keras",
    monitor="val_accuracy", save_best_only=True, verbose=1
)

print("\nCalculando pesos de classes para balanceamento da Matriz de Confusão...")
classes_unicas = np.unique(y_train)
pesos_balanceados = compute_class_weight(class_weight='balanced', classes=classes_unicas, y=y_train)
class_weights_dict = { cl: pesos_balanceados[i] for i, cl in enumerate(classes_unicas) }
print("Pesos:", class_weights_dict)

print("\nTreinando...")
hist = modelo.fit(
    X_train, y_train,
    epochs=150, batch_size=8,
    validation_split=0.2,
    class_weight=class_weights_dict,
    callbacks=[early_stop, checkpoint],
    verbose=1
)

loss, acc = modelo.evaluate(X_test, y_test, verbose=0)
print(f"\nAvaliando no conjunto de teste...")
print(f"  Loss    : {loss:.4f}")
print(f"  Accuracy: {acc * 100:.1f}%")

# Matriz de confusão rápida
from sklearn.metrics import classification_report
y_pred = np.argmax(modelo.predict(X_test, verbose=0), axis=1)
print("\nRelatório por classe:")
print(classification_report(y_test, y_pred, target_names=encoder.classes_))

def classificar(texto):
    t = re.sub(r"[^a-záàãâéêíóôõúüç\s]", " ", texto.lower())
    v = vectorizer.transform([t]).toarray()
    p = modelo.predict(v, verbose=0)
    i = np.argmax(p)
    return encoder.classes_[i], p[0][i] * 100

print("\nTeste manual:")
exemplos = [
    "O titular tem direito à exclusão de seus dados pessoais.",
    "Acórdão: por unanimidade, negado provimento ao recurso especial.",
    "Cláusula segunda: o pagamento será feito até o décimo dia do mês.",
    "Excelentíssimo Senhor Juiz, vem o requerente propor a presente ação.",
    "O princípio da legalidade é fundamento do Estado Democrático de Direito.",
]
for t in exemplos:
    c, conf = classificar(t)
    print(f"  [{c.upper():10s}] {conf:5.1f}%  ->  {t[:60]}...")

# Gráfico
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(hist.history["accuracy"],     label="Treino")
ax1.plot(hist.history["val_accuracy"], label="Validação")
ax1.set_title("Acurácia"); ax1.legend(); ax1.grid(alpha=0.3)
ax2.plot(hist.history["loss"],     label="Treino")
ax2.plot(hist.history["val_loss"], label="Validação")
ax2.set_title("Loss"); ax2.legend(); ax2.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("models/grafico_treinamento.png", dpi=150)
print("\nGráfico salvo.")
modelo.save_weights("models/modelo_juridico.weights.h5")
print("Pesos salvos em models/modelo_juridico.weights.h5")