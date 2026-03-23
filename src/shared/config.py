# src/shared/config.py
# Configurações centralizadas do projeto — todas as constantes em um único lugar

from pathlib import Path

# ─── Raiz do projeto ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent

# ─── Caminhos de dados ────────────────────────────────────────────────────────
DATA_DIR           = ROOT / "data"
DATA_RAW_DIR       = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATASET_PATH       = DATA_RAW_DIR / "dataset_juridico.json"

VECTORIZER_PATH    = DATA_PROCESSED_DIR / "vectorizer.pkl"
ENCODER_PATH       = DATA_PROCESSED_DIR / "encoder.pkl"
X_TRAIN_PATH       = DATA_PROCESSED_DIR / "X_train.npy"
X_TEST_PATH        = DATA_PROCESSED_DIR / "X_test.npy"
Y_TRAIN_PATH       = DATA_PROCESSED_DIR / "y_train.npy"
Y_TEST_PATH        = DATA_PROCESSED_DIR / "y_test.npy"

# ─── Caminhos de modelos ──────────────────────────────────────────────────────
MODELS_DIR         = ROOT / "models"
TFLITE_DIR         = MODELS_DIR / "tflite"
RELATORIO_DIR      = MODELS_DIR / "relatorio"
PRUNING_LOGS_DIR   = MODELS_DIR / "pruning_logs"

MODEL_KERAS_PATH   = MODELS_DIR / "modelo_juridico.keras"
MODEL_WEIGHTS_PATH = MODELS_DIR / "modelo_juridico.weights.h5"
MODEL_TFLITE_PATH  = TFLITE_DIR / "modelo_juridico.tflite"
MODEL_INT8_PATH    = TFLITE_DIR / "modelo_juridico_int8.tflite"
MODEL_PRUNED_PATH  = TFLITE_DIR / "modelo_pruned_final.tflite"
GRAFICO_TREINO_PATH = MODELS_DIR / "grafico_treinamento.png"

# ─── Hiperparâmetros de pré-processamento ─────────────────────────────────────
TFIDF_MAX_FEATURES = 3000
TFIDF_NGRAM_RANGE  = (1, 2)
TFIDF_MIN_DF       = 1
TFIDF_SUBLINEAR_TF = True

# ─── Hiperparâmetros de treino ────────────────────────────────────────────────
RANDOM_SEED        = 42
TEST_SIZE          = 0.2
TRAIN_BATCH_SIZE   = 32          # Era 8 — alterado para convergência mais estável
TRAIN_EPOCHS       = 150
EARLY_STOPPING_PATIENCE = 20
EARLY_STOPPING_MONITOR  = "val_accuracy"

# ─── Hiperparâmetros do quantizador INT8 ─────────────────────────────────────
INT8_REPRESENTATIVE_SAMPLES = 50

# ─── Informações do projeto ───────────────────────────────────────────────────
PROJECT_NAME   = "Edge AI Jurídico"
PROJECT_AUTHOR = "Caio R."
PROJECT_ADVISOR = "Prof. Msc. Afonso Calábria"
PROJECT_INSTITUTION = "UNISSAU"
PROJECT_YEAR   = 2026
