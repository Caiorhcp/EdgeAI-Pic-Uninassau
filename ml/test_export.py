"""Testes do pré-processamento e geração das fixtures do teste de paridade do TypeScript.
A paridade JSON x scikit-learn é verificada no próprio train.py, logo após exportar."""

import json

import numpy as np
import pandas as pd
import pytest

from train import DATA, OUT_MODEL, normalize, predict_from_json

FIXTURES = OUT_MODEL.parent.parent / "src" / "lib" / "__fixtures__" / "parity.json"


def test_normalize():
    assert normalize("Tribunal de Justiça do Rio") == ["tribunal", "justiça", "rio"]
    assert normalize("contato: joao@ex.com, www.stf.jus.br") == ["contato", "email", "site"]
    assert normalize("Lei 11.419/2006, Art. 5º") == ["lei", "art"]


@pytest.mark.skipif(not OUT_MODEL.exists(), reason="rode python train.py antes")
def test_write_ts_fixtures():
    model = json.loads(OUT_MODEL.read_text(encoding="utf-8"))
    texts = pd.read_parquet(DATA / "test.parquet", columns=["body"]).body.sample(20, random_state=0)
    cases = [{"text": t, "probs": np.round(predict_from_json(model, t), 6).tolist()} for t in texts]
    FIXTURES.parent.mkdir(parents=True, exist_ok=True)
    FIXTURES.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
