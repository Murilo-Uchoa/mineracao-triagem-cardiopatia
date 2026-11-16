import numpy as np
import pandas as pd
import pytest

import config
import interpretacao


def test_matriz_confusao_com_limiar_por_linha():
    y = np.array([1, 1, 0, 0, 1])
    proba = np.array([0.6, 0.3, 0.4, 0.7, 0.2])
    limiar = np.array([0.5, 0.5, 0.5, 0.5, 0.1])   # última linha: outro fold
    m = interpretacao.matriz_confusao(y, proba, limiar)
    assert m == {"tp": 2, "fn": 1, "fp": 1, "tn": 1}
    assert sum(m.values()) == len(y)


def test_agregar_importancia():
    folds = [{"importancia": {"Peso": 0.02, "FC": 0.00}},
             {"importancia": {"Peso": 0.04, "FC": 0.02}}]
    agg = interpretacao.agregar_importancia(folds)
    assert agg["Peso"]["media"] == pytest.approx(0.03)
    assert agg["Peso"]["dp"] == pytest.approx(np.std([0.02, 0.04], ddof=1))
    assert list(agg) == ["Peso", "FC"]   # ordenado pela média, decrescente


def test_taxa_fn_por_grupo():
    y = np.array([1, 1, 1, 0, 1])
    pred = np.array([0, 1, 0, 0, 1])
    grupo = pd.Series(["A", "A", "B", "B", "B"])
    t = interpretacao.taxa_fn_por_grupo(y, pred, grupo)
    assert t["A"] == {"positivos": 2, "fn": 1, "taxa_fn": 0.5}
    assert t["B"] == {"positivos": 2, "fn": 1, "taxa_fn": 0.5}


def test_rodar_com_resultados_reais():
    # previsoes_oof.csv é gravado por último, quando os quatro modelos terminam.
    if not (config.RESULTADOS / "previsoes_oof.csv").exists():
        pytest.skip("validação aninhada ainda não rodou")
    import base_dados
    X, y, _, base = base_dados.carregar_base(config.RAW)
    res = interpretacao.rodar(X, y, base, destino=None)
    for chave in ("matriz_05", "matriz_triagem"):
        assert sum(res[chave].values()) == 11454
    assert set(res["importancia"][res["melhor"]]) == set(config.ATRIBUTOS)
    assert res["melhor"] != "dummy"


def test_perfil_por_sopro_e_subanalise():
    if not (config.RESULTADOS / "previsoes_oof.csv").exists():
        pytest.skip("validação aninhada ainda não rodou")
    import base_dados
    X, y, _, base = base_dados.carregar_base(config.RAW)
    res = interpretacao.rodar(X, y, base, destino=None)
    s = res["perfil_fn_05"]["sopro"]
    assert set(s) == {"com sopro", "sem sopro"}
    # Revisão final: o modelo erra proporcionalmente MAIS nas cardiopatias sem sopro.
    assert s["sem sopro"]["taxa_fn"] > s["com sopro"]["taxa_fn"]
    sub = res["sem_cardiopatia_estabelecida"]
    assert sub["n"] == 11454 - 1114
    assert 0.75 < sub["auc_roc"] < 0.79
    assert 0 < sub["sensibilidade_triagem"] < 1 and 0 < sub["especificidade_triagem"] < 1
