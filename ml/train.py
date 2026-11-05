"""Treina o classificador de tipo de documento no VICTOR Small (STF) e exporta para JSON.

Uso: python ml/train.py            (espera data/victor/{train,validation,test}.parquet)

O JSON exportado é lido pelo site, que faz a inferência no navegador. Por isso o
pré-processamento (normalize) precisa ser idêntico ao de web/src/lib/classifier.ts.
"""

import json
import re
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score, classification_report, confusion_matrix, f1_score, recall_score,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "victor"
OUT_MODEL = ROOT / "web" / "public" / "model.json"
OUT_METRICS = ROOT / "ml" / "metrics.json"

# Palavras que o VICTOR já removeu de forma parcial; removê-las nos dois lados evita diferença treino/uso.
STOPWORDS = {"a", "o", "as", "os", "de", "do", "da", "em", "e", "no", "na", "ou", "um", "é", "ao", "à"}
TOKEN_RE = re.compile(r"[a-zà-öø-ÿ]+")
EMAIL_RE = re.compile(r"\S+@\S+")
URL_RE = re.compile(r"(https?://|www\.)\S+")

LABELS = {
    "acordao_de_2_instancia": "Acórdão",
    "agravo_em_recurso_extraordinario": "Agravo em RE",
    "despacho_de_admissibilidade": "Despacho",
    "peticao_do_RE": "Petição de RE",
    "sentenca": "Sentença",
    "outros": "Outros",
}

# Baseline publicado (Luz de Araujo et al., LREC 2020, Tabela 2, SVic, F1 por página)
PAPER_SVIC = {"SVM": {"macro": 76.32, "weighted": 94.25}, "CNN": {"macro": 75.84, "weighted": 94.72}}


def normalize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text.lower())
    text = URL_RE.sub(" site ", EMAIL_RE.sub(" email ", text))
    return [t for t in TOKEN_RE.findall(text) if len(t) > 1 and t not in STOPWORDS]


def load(split: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{split}.parquet", columns=["process_id", "document_type", "body"])


MAX_FEATURES = 30_000  # 70k dá o mesmo F1 (77,7 vs 77,6) com o dobro do tamanho no navegador


def make_vectorizer() -> TfidfVectorizer:
    # Mesma configuração do artigo: uni+bigramas, min_df=2, max_df=0.5
    return TfidfVectorizer(
        tokenizer=normalize, lowercase=False, token_pattern=None,
        ngram_range=(1, 2), min_df=2, max_df=0.5, max_features=MAX_FEATURES,
        sublinear_tf=True, dtype=np.float32,
    )


def export(vec, clf, prior: np.ndarray, path: Path) -> None:
    vocab = vec.vocabulary_
    terms = sorted(vocab, key=vocab.get)  # índice i -> termo
    model = {
        "version": 1,
        "stopwords": sorted(STOPWORDS),
        "classes": list(clf.classes_),
        "labels": [LABELS[c] for c in clf.classes_],
        "terms": terms,
        "idf": np.round(vec.idf_, 4).tolist(),
        # coef[t] = pesos do termo t para cada classe (linha por termo deixa o JSON fácil de indexar)
        "coef": np.round(clf.coef_.T, 4).tolist(),
        "intercept": np.round(clf.intercept_, 4).tolist(),
        "prior": np.round(prior, 6).tolist(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def predict_from_json(model: dict, text: str) -> np.ndarray:
    """Inferência só com o JSON exportado: o mesmo algoritmo de web/src/lib/classifier.ts."""
    index = model.setdefault("_index", {t: i for i, t in enumerate(model["terms"])})
    tokens = normalize(text)
    grams = [g for g in tokens + [f"{a} {b}" for a, b in zip(tokens, tokens[1:])] if g in index]
    counts: dict[int, int] = {}
    for g in grams:
        counts[index[g]] = counts.get(index[g], 0) + 1
    x = {i: (1 + np.log(c)) * model["idf"][i] for i, c in counts.items()}
    norm = np.sqrt(sum(v * v for v in x.values())) or 1.0
    logits = np.array(model["intercept"], dtype=float)
    for i, v in x.items():
        logits += np.array(model["coef"][i]) * (v / norm)
    e = np.exp(logits - logits.max())
    return e / e.sum()


def check_parity(vec, clf, texts: pd.Series) -> None:
    model = json.loads(OUT_MODEL.read_text(encoding="utf-8"))
    expected = clf.predict_proba(vec.transform(texts))
    got = np.array([predict_from_json(model, t) for t in texts])
    diff = np.abs(expected - got).max()
    assert diff < 1e-2, f"inferência via JSON difere do scikit-learn (máx {diff:.4f})"
    print(f"paridade JSON x scikit-learn OK em {len(texts)} páginas (diferença máx {diff:.5f})")


def main() -> None:
    train, val, test = load("train"), load("validation"), load("test")
    # As partições do VICTOR são por processo; conferir garante que não há vazamento entre elas.
    assert not set(train.process_id) & set(test.process_id), "processo repetido entre treino e teste"
    assert not set(val.process_id) & set(test.process_id), "processo repetido entre validação e teste"

    vec = make_vectorizer()
    X_train, X_val = vec.fit_transform(train.body), vec.transform(val.body)

    # Sem class_weight: com "balanced" o F1 macro caiu de 0,77 para 0,70 (excesso de falsos positivos nas classes raras)
    best = None
    for C in (30.0, 100.0):
        t = time.time()
        clf = LogisticRegression(C=C, max_iter=300).fit(X_train, train.document_type)
        f1 = f1_score(val.document_type, clf.predict(X_val), average="macro")
        print(f"C={C}: F1 macro (validação) = {f1:.4f} [{time.time() - t:.0f}s]")
        if best is None or f1 > best[0]:
            best = (f1, C, clf)

    _, C, clf = best
    X_test = vec.transform(test.body)
    y_pred = clf.predict(X_test)

    # O site recebe uma peça por vez, não um processo com 90% de "outros". Dividir pela
    # frequência de treino equivale a supor classes igualmente prováveis; a métrica certa
    # nesse cenário é o recall médio (acurácia balanceada).
    prior = np.array([(train.document_type == c).mean() for c in clf.classes_])
    y_uniform = clf.classes_[(clf.predict_proba(X_test) / prior).argmax(1)]
    report = classification_report(test.document_type, y_pred, output_dict=True, digits=4)
    print(classification_report(test.document_type, y_pred, digits=4))

    metrics = {
        "dataset": "VICTOR Small (STF, LREC 2020), F1 por página",
        "params": {"max_features": MAX_FEATURES, "C": C, "ngram_range": [1, 2]},
        "n": {"train": len(train), "validation": len(val), "test": len(test)},
        "test": {
            "accuracy": report["accuracy"],
            "f1_macro": report["macro avg"]["f1-score"],
            "f1_weighted": report["weighted avg"]["f1-score"],
            "per_class": {c: report[c]["f1-score"] for c in clf.classes_},
            "balanced_accuracy": balanced_accuracy_score(test.document_type, y_pred),
        },
        "test_uniform_prior": {
            "f1_macro": f1_score(test.document_type, y_uniform, average="macro"),
            "balanced_accuracy": balanced_accuracy_score(test.document_type, y_uniform),
            "recall_per_class": dict(zip(clf.classes_, recall_score(test.document_type, y_uniform, average=None))),
        },
        "confusion_matrix": {"labels": list(clf.classes_),
                             "matrix": confusion_matrix(test.document_type, y_pred, labels=clf.classes_).tolist()},
        "paper_baseline_svic": PAPER_SVIC,
    }
    OUT_METRICS.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    export(vec, clf, prior, OUT_MODEL)
    print(f"modelo: {OUT_MODEL} ({OUT_MODEL.stat().st_size / 1e6:.1f} MB)")
    check_parity(vec, clf, test.body.sample(500, random_state=0))


if __name__ == "__main__":
    main()
