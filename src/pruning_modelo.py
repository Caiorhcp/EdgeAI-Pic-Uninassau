# src/pruning_modelo.py
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "2"

import numpy as np
import time
import tensorflow as tf

print("Carregando dados...")
X_train = np.load("data/processed/X_train.npy").astype(np.float32)
X_test  = np.load("data/processed/X_test.npy").astype(np.float32)
y_train = np.load("data/processed/y_train.npy")
y_test  = np.load("data/processed/y_test.npy")
INPUT_DIM = X_train.shape[1]

def construir_e_treinar(verbose=0):
    m = tf.keras.Sequential([
        tf.keras.layers.Dense(256, activation="relu", input_shape=(INPUT_DIM,)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(5, activation="softmax"),
    ])
    m.compile(
        optimizer=tf.keras.optimizers.Adam(0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    m.fit(
        X_train, y_train,
        epochs=150, batch_size=8,
        validation_split=0.2,
        callbacks=[tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=20,
            restore_best_weights=True, verbose=0
        )],
        verbose=verbose
    )
    return m

def aplicar_pruning(modelo, esparsidade):
    total = zerados = 0
    for layer in modelo.layers:
        if not isinstance(layer, tf.keras.layers.Dense):
            continue
        pesos, bias = layer.get_weights()
        threshold   = np.percentile(np.abs(pesos), esparsidade * 100)
        mascara     = np.abs(pesos) >= threshold
        layer.set_weights([pesos * mascara, bias])
        zerados += int(np.sum(~mascara))
        total   += pesos.size
    print(f"  Pesos zerados: {zerados:,}/{total:,} ({zerados/total*100:.1f}%)")

def para_tflite(modelo):
    def rep():
        for i in range(min(50, len(X_test))):
            yield [X_test[i:i+1]]
    c = tf.lite.TFLiteConverter.from_keras_model(modelo)
    c.optimizations = [tf.lite.Optimize.DEFAULT]
    c.representative_dataset = rep
    c.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    c.inference_input_type  = tf.float32
    c.inference_output_type = tf.float32
    return c.convert()

def benchmark(tflite_bytes, n=500):
    interp = tf.lite.Interpreter(model_content=tflite_bytes)
    interp.allocate_tensors()
    inp = interp.get_input_details()
    out = interp.get_output_details()
    t0  = time.time()
    for _ in range(n):
        interp.set_tensor(inp[0]["index"], X_test[0:1])
        interp.invoke()
        interp.get_tensor(out[0]["index"])
    return (time.time() - t0) / n * 1000

os.makedirs("models/tflite", exist_ok=True)

# ─── Modelo base ──────────────────────────────────────────────────────────────
print("Treinando modelo base...")
base = construir_e_treinar()
_, acc_base = base.evaluate(X_test, y_test, verbose=0)
base.save_weights("models/pesos_base.weights.h5")

tflite_base = para_tflite(base)
with open("models/tflite/modelo_base_ref.tflite", "wb") as f:
    f.write(tflite_base)
tam_base = os.path.getsize("models/tflite/modelo_base_ref.tflite") / 1024
ms_base  = benchmark(tflite_base)

print(f"Base → acurácia: {acc_base*100:.1f}% | tamanho: {tam_base:.1f} KB | latência: {ms_base:.3f} ms\n")

# ─── Pruning em 4 níveis ──────────────────────────────────────────────────────
niveis    = [0.30, 0.50, 0.70, 0.90]
resultados = []

for esp in niveis:
    print(f"Esparsidade {int(esp*100)}%:")
    m = construir_e_treinar()
    m.load_weights("models/pesos_base.weights.h5")
    aplicar_pruning(m, esp)

    m.compile(
        optimizer=tf.keras.optimizers.Adam(0.0005),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    m.fit(
        X_train, y_train,
        epochs=20, batch_size=8,
        validation_split=0.2,
        callbacks=[tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=8,
            restore_best_weights=True, verbose=0
        )],
        verbose=0
    )

    _, acc = m.evaluate(X_test, y_test, verbose=0)
    tb     = para_tflite(m)
    caminho = f"models/tflite/modelo_pruned_{int(esp*100)}.tflite"
    with open(caminho, "wb") as f:
        f.write(tb)
    tam = os.path.getsize(caminho) / 1024
    ms  = benchmark(tb)

    resultados.append({"esp": int(esp*100), "acc": acc*100, "tam": tam, "ms": ms})
    print(f"  Acurácia : {acc*100:.1f}%")
    print(f"  Tamanho  : {tam:.1f} KB")
    print(f"  Latência : {ms:.3f} ms\n")

# ─── Resumo ───────────────────────────────────────────────────────────────────
limite    = acc_base * 100 - 5.0
candidatos = [r for r in resultados if r["acc"] >= limite]
melhor     = max(candidatos, key=lambda r: r["esp"]) if candidatos else resultados[0]

print("=" * 56)
print("RESUMO — Pruning por magnitude")
print("=" * 56)
print(f"{'Esparsidade':>12} {'Acurácia':>10} {'Tamanho':>10} {'Redução':>9}")
print("-" * 56)
print(f"{'Base (0%)':>12}  {acc_base*100:>8.1f}%  {tam_base:>8.1f} KB       —")
for r in resultados:
    red  = (1 - r["tam"] / tam_base) * 100
    flag = "  ← MELHOR" if r["esp"] == melhor["esp"] else ""
    print(f"{r['esp']:>11}%  {r['acc']:>8.1f}%  {r['tam']:>8.1f} KB  {red:>6.1f}%{flag}")
print("=" * 56)

import shutil
shutil.copy(
    f"models/tflite/modelo_pruned_{melhor['esp']}.tflite",
    "models/tflite/modelo_pruned_final.tflite"
)
print(f"\nMelhor modelo salvo → models/tflite/modelo_pruned_final.tflite")