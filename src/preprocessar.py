# src/preprocessar.py — versão TF-IDF
import os, json, re, pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

print("Carregando dataset...")
with open("data/raw/dataset_juridico.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

textos  = [d["texto"]  for d in dados]
classes = [d["classe"] for d in dados]
print(f"Total: {len(textos)} amostras | Classes: {set(classes)}")

def limpar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-záàãâéêíóôõúüç\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()

textos_limpos = [limpar(t) for t in textos]

# TF-IDF: pondera palavras pela raridade — "titular" vale mais que "o"
vectorizer = TfidfVectorizer(
    max_features=3000,
    ngram_range=(1, 2),   # unigramas + bigramas ("dados pessoais", "recurso especial")
    min_df=1,
    sublinear_tf=True
)
X = vectorizer.fit_transform(textos_limpos).toarray()

encoder = LabelEncoder()
y = encoder.fit_transform(classes)

print(f"\nMapeamento:")
for i, c in enumerate(encoder.classes_):
    print(f"  {i} → {c}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nShape X: {X.shape}")
print(f"Treino : {X_train.shape[0]} | Teste: {X_test.shape[0]}")

os.makedirs("data/processed", exist_ok=True)
np.save("data/processed/X_train.npy", X_train)
np.save("data/processed/X_test.npy",  X_test)
np.save("data/processed/y_train.npy", y_train)
np.save("data/processed/y_test.npy",  y_test)

with open("data/processed/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)
with open("data/processed/encoder.pkl", "wb") as f:
    pickle.dump(encoder, f)

print("\nPré-processamento concluído!")