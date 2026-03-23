# pipeline/05_preprocessar.py — usa shared/config para caminhos centralizados
import os, sys, json, pickle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from src.infrastructure.ml.preprocessor import limpar_texto
from src.shared.config import (
    DATASET_PATH, DATA_PROCESSED_DIR,
    X_TRAIN_PATH, X_TEST_PATH, Y_TRAIN_PATH, Y_TEST_PATH,
    VECTORIZER_PATH, ENCODER_PATH,
    TFIDF_MAX_FEATURES, TFIDF_NGRAM_RANGE, TFIDF_MIN_DF, TFIDF_SUBLINEAR_TF,
    RANDOM_SEED, TEST_SIZE,
)

print("Carregando dataset…")
with open(str(DATASET_PATH), "r", encoding="utf-8") as f:
    dados = json.load(f)

textos  = [d["texto"]  for d in dados]
classes = [d["classe"] for d in dados]
print(f"Total: {len(textos)} amostras | Classes: {set(classes)}")

textos_limpos = [limpar_texto(t) for t in textos]

vectorizer = TfidfVectorizer(
    max_features=TFIDF_MAX_FEATURES,
    ngram_range=TFIDF_NGRAM_RANGE,
    min_df=TFIDF_MIN_DF,
    sublinear_tf=TFIDF_SUBLINEAR_TF,
)
from typing import Any as _Any
_tfidf_fit: _Any = vectorizer.fit_transform(textos_limpos)
# pyright: ignore[reportAttributeAccessIssue]
X = getattr(_tfidf_fit, "toarray", lambda: _tfidf_fit)() if hasattr(_tfidf_fit, "toarray") else _tfidf_fit

encoder = LabelEncoder()
y = encoder.fit_transform(classes)

print(f"\nMapeamento:")
for i, c in enumerate(list(encoder.classes_)):  # type: ignore[arg-type]
    print(f"  {i} → {c}")

X_train: np.ndarray
X_test: np.ndarray
y_train: np.ndarray
y_test: np.ndarray
X_train, X_test, y_train, y_test = train_test_split(  # type: ignore[assignment]
    X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
)
print(f"\nShape X: {X.shape}")
print(f"Treino: {X_train.shape[0]} | Teste: {X_test.shape[0]}")

os.makedirs(str(DATA_PROCESSED_DIR), exist_ok=True)
np.save(str(X_TRAIN_PATH), X_train)
np.save(str(X_TEST_PATH),  X_test)
np.save(str(Y_TRAIN_PATH), y_train)
np.save(str(Y_TEST_PATH),  y_test)
with open(str(VECTORIZER_PATH), "wb") as f: pickle.dump(vectorizer, f)
with open(str(ENCODER_PATH),    "wb") as f: pickle.dump(encoder, f)
print("\nPré-processamento concluído!")
