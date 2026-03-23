# src/infrastructure/ml/tflite_classificador.py
# Adaptador de infraestrutura — implementa IClassificadorRepository com TFLite

import os
import pickle
import time
from typing import Dict

import numpy as np

from src.domain.repositories.i_classificador_repository import IClassificadorRepository
from src.domain.value_objects.classe_documento import ClasseDocumento
from src.domain.value_objects.resultado_classificacao import ResultadoClassificacao
from src.infrastructure.ml.preprocessor import limpar_texto
from src.shared.config import MODEL_INT8_PATH, VECTORIZER_PATH, ENCODER_PATH
from src.shared.exceptions import ModeloNaoEncontradoError, ArtefatoNaoEncontradoError
from src.shared.logger import get_logger

logger = get_logger(__name__)


class TFLiteClassificador(IClassificadorRepository):
    """
    Implementação concreta do classificador usando TensorFlow Lite INT8.
    Segue o padrão Adapter — faz a ponte entre o domínio e o TFLite.
    """

    def __init__(
        self,
        model_path: str | None = None,
        vectorizer_path: str | None = None,
        encoder_path: str | None = None,
    ):
        # Suporte a paths customizados (útil em testes)
        _model_path:      str = model_path if model_path is not None else str(MODEL_INT8_PATH)
        _vectorizer_path: str = vectorizer_path if vectorizer_path is not None else str(VECTORIZER_PATH)
        _encoder_path:    str = encoder_path if encoder_path is not None else str(ENCODER_PATH)

        self._carregar_modelo(_model_path)
        self._carregar_artefatos(_vectorizer_path, _encoder_path)
        logger.info("TFLiteClassificador inicializado com sucesso.")

    def _carregar_modelo(self, model_path: str) -> None:
        import tensorflow as tf  # Import tardio — evita overhead desnecessário

        if not os.path.exists(model_path):
            raise ModeloNaoEncontradoError(model_path)

        self._interpreter = tf.lite.Interpreter(model_path=model_path, num_threads=4)
        self._interpreter.allocate_tensors()
        self._inp_details = self._interpreter.get_input_details()
        self._out_details = self._interpreter.get_output_details()
        logger.info("Modelo TFLite carregado: %s", model_path)

    def _carregar_artefatos(self, vectorizer_path: str, encoder_path: str) -> None:
        if not os.path.exists(vectorizer_path):
            raise ArtefatoNaoEncontradoError(vectorizer_path)
        if not os.path.exists(encoder_path):
            raise ArtefatoNaoEncontradoError(encoder_path)

        with open(vectorizer_path, "rb") as f:
            self._vectorizer = pickle.load(f)
        with open(encoder_path, "rb") as f:
            self._encoder = pickle.load(f)

        logger.info("Artefatos carregados: vectorizer + encoder (%d classes)",
                    len(self._encoder.classes_))

    def classificar(self, texto: str) -> ResultadoClassificacao:
        """
        Classifica um texto jurídico usando TFLite INT8.

        Args:
            texto: Texto bruto do documento

        Returns:
            ResultadoClassificacao com classe, confiança e probabilidades
        """
        t0 = time.perf_counter()

        texto_limpo = limpar_texto(texto)
        vetor = self._vectorizer.transform([texto_limpo]).toarray().astype(np.float32)

        self._interpreter.set_tensor(self._inp_details[0]["index"], vetor)
        self._interpreter.invoke()
        probs = self._interpreter.get_tensor(self._out_details[0]["index"])[0]

        ms = (time.perf_counter() - t0) * 1000
        idx = int(np.argmax(probs))
        classe_str = self._encoder.classes_[idx]

        probabilidades: Dict[str, float] = {
            self._encoder.classes_[i]: float(probs[i])
            for i in range(len(probs))
        }

        return ResultadoClassificacao(
            classe=ClasseDocumento.from_string(classe_str),
            confianca=float(probs[idx]) * 100,
            probabilidades=probabilidades,
            ms_inferencia=ms,
        )

    @property
    def classes(self):
        """Retorna as classes do encoder."""
        return list(self._encoder.classes_)
