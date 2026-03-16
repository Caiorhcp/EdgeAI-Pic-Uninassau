# src/converter_tflite.py
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import re, pickle
import numpy as np
import tensorflow as tf

# ─── 1. Carregar modelo e artefatos ──────────────────────────────────────────
print("Carregando modelo treinado...")
modelo = tf.keras.models.load_model("models/modelo_juridico.keras")

with open("data/processed/vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)
with open("data/processed/encoder.pkl", "rb") as f:
    encoder = pickle.load(f)

# ─── 2. Converter para TFLite (sem quantização primeiro) ─────────────────────
print("\nConvertendo para TFLite...")
os.makedirs("models/tflite", exist_ok=True)

converter = tf.lite.TFLiteConverter.from_keras_model(modelo)
tflite_model = converter.convert()

caminho_base = "models/tflite/modelo_juridico.tflite"
with open(caminho_base, "wb") as f:
    f.write(tflite_model)

tamanho_original = os.path.getsize("models/modelo_juridico.keras") / 1024
tamanho_tflite   = os.path.getsize(caminho_base) / 1024
print(f"  Modelo Keras  : {tamanho_original:.1f} KB")
print(f"  Modelo TFLite : {tamanho_tflite:.1f} KB")

# ─── 3. Converter com quantização INT8 (ainda menor para edge) ───────────────
print("\nAplicando quantização INT8...")

X_test = np.load("data/processed/X_test.npy").astype(np.float32)

def dataset_representativo():
    for i in range(min(50, len(X_test))):
        yield [X_test[i:i+1]]

converter_q = tf.lite.TFLiteConverter.from_keras_model(modelo)
converter_q.optimizations = [tf.lite.Optimize.DEFAULT]
converter_q.representative_dataset = dataset_representativo
converter_q.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter_q.inference_input_type  = tf.float32
converter_q.inference_output_type = tf.float32

tflite_model_q = converter_q.convert()

caminho_q = "models/tflite/modelo_juridico_int8.tflite"
with open(caminho_q, "wb") as f:
    f.write(tflite_model_q)

tamanho_q = os.path.getsize(caminho_q) / 1024
print(f"  Modelo INT8   : {tamanho_q:.1f} KB")
print(f"  Redução       : {(1 - tamanho_q/tamanho_tflite)*100:.1f}%")

# ─── 4. Testar inferência com o modelo TFLite ────────────────────────────────
print("\nTestando inferência com TFLite...")

interpreter = tf.lite.Interpreter(model_path=caminho_q)
interpreter.allocate_tensors()

input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print(f"  Input shape : {input_details[0]['shape']}")
print(f"  Output shape: {output_details[0]['shape']}")

def classificar_tflite(texto):
    t = re.sub(r"[^a-záàãâéêíóôõúüç\s]", " ", texto.lower())
    v = vectorizer.transform([t]).toarray().astype(np.float32)

    interpreter.set_tensor(input_details[0]['index'], v)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]['index'])
    idx    = np.argmax(output)
    return encoder.classes_[idx], output[0][idx] * 100

print("\nClassificação via TFLite (simulando dispositivo edge):")
exemplos = [
    ("lgpd",     "O titular tem direito à exclusão de seus dados pessoais."),
    ("acordao",  "Acórdão: por unanimidade, negado provimento ao recurso especial."),
    ("contrato", "Cláusula segunda: o pagamento será feito até o décimo dia do mês."),
    ("peticao",  "Excelentíssimo Senhor Juiz, vem o requerente propor a presente ação."),
    ("outro",    "O princípio da legalidade é fundamento do Estado Democrático de Direito."),
]

acertos = 0
for esperado, texto in exemplos:
    classe, confianca = classificar_tflite(texto)
    ok = "✓" if classe == esperado else "✗"
    if classe == esperado:
        acertos += 1
    print(f"  {ok} [{classe.upper():10s}] {confianca:5.1f}%  →  {texto[:55]}...")

print(f"\nAcertos: {acertos}/{len(exemplos)}")

# ─── 5. Benchmark de velocidade ──────────────────────────────────────────────
import time

print("\nBenchmark de velocidade (100 inferências):")
texto_teste = "O titular tem direito à exclusão de seus dados pessoais."
t_limpo = re.sub(r"[^a-záàãâéêíóôõúüç\s]", " ", texto_teste.lower())
v_teste  = vectorizer.transform([t_limpo]).toarray().astype(np.float32)

inicio = time.time()
for _ in range(100):
    interpreter.set_tensor(input_details[0]['index'], v_teste)
    interpreter.invoke()
    _ = interpreter.get_tensor(output_details[0]['index'])
fim = time.time()

ms_por_inferencia = (fim - inicio) / 100 * 1000
print(f"  Tempo médio por inferência: {ms_por_inferencia:.2f} ms")
print(f"  Inferências por segundo   : {1000/ms_por_inferencia:.0f}")

# ─── 6. Resumo final ─────────────────────────────────────────────────────────
print("\n" + "="*50)
print("RESUMO — Modelos gerados:")
print(f"  Keras  (treino) : {tamanho_original:.1f} KB")
print(f"  TFLite (base)   : {tamanho_tflite:.1f} KB")
print(f"  TFLite (INT8)   : {tamanho_q:.1f} KB  ← deploy no edge")
print(f"  Velocidade      : {ms_por_inferencia:.2f} ms/inferência")
print("="*50)
print("\nArquivos prontos para deploy em models/tflite/")