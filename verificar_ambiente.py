import os
# Silenciar os logs verbosos do TensorFlow (OneDNN e Debugs básicos)
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
import sklearn
import numpy as np
import pandas as pd

def verificar():
    print("=" * 45)
    print(f"TensorFlow:   {tf.__version__}")
    print(f"Scikit-learn: {sklearn.__version__}")
    print(f"NumPy:        {np.__version__}")
    print(f"Pandas:       {pd.__version__}")
    print("=" * 45)

    try:
        # Teste rápido: cria um tensor simples no TF para verificar o core engine
        tensor_teste = tf.constant([[1, 2], [3, 4]])
        print(f"\nTensor de teste criado com sucesso:")
        print(tensor_teste)
        print("\nAmbiente pronto!")
    except Exception as e:
        print(f"\nErro no carregamento primário do TensorFlow: {e}")

if __name__ == "__main__":
    verificar()