import tensorflow as tf
import sklearn
import numpy as np
import pandas as pd

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
# ... resto do código

print("=" * 45)
print(f"TensorFlow:  {tf.__version__}")
print(f"Scikit-learn: {sklearn.__version__}")
print(f"NumPy:        {np.__version__}")
print(f"Pandas:       {pd.__version__}")
print("=" * 45)

# Teste rápido: cria um tensor simples
tensor_teste = tf.constant([[1, 2], [3, 4]])
print(f"\nTensor de teste criado com sucesso:")
print(tensor_teste)
print("\nAmbiente pronto!")