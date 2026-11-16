from functools import lru_cache

import numpy as np

import base_dados
import config
import experimento
import modelos


@lru_cache(maxsize=1)
def _base():
    return base_dados.carregar_base(config.RAW)


@lru_cache(maxsize=1)
def _amostra():
    X, y, grupos, _ = _base()
    idx = np.sort(np.random.default_rng(0).choice(len(y), 1500, replace=False))
    return X.iloc[idx].reset_index(drop=True), y[idx], grupos[idx]


def test_modelos_tem_grades_do_design():
    assert modelos.NOMES == ["dummy", "logistica", "random_forest", "gradient_boosting"]
    assert modelos.GRADES["logistica"]["modelo__C"] == [0.01, 0.1, 1, 10]
    for nome in modelos.NOMES:
        assert list(modelos.montar_pipeline(nome).named_steps) == ["prep", "modelo"]


def test_particoes_externas_sem_paciente_dos_dois_lados():
    _, y, grupos, _ = _base()
    for treino, teste in experimento.particoes(y, grupos, 10, config.SEED):
        assert not set(grupos[treino]) & set(grupos[teste])


def test_particoes_internas_sem_sobreposicao():
    X, y, g = _amostra()
    res = experimento.validacao_aninhada("logistica", X, y, g, n_externo=3, n_interno=2,
                                         registrar_particoes=True, importancia=False)
    assert res["sobreposicoes_internas"] and all(n == 0 for n in res["sobreposicoes_internas"])


def test_reprodutivel():
    X, y, g = _amostra()
    a = experimento.validacao_aninhada("gradient_boosting", X, y, g, n_externo=3,
                                       n_interno=2, importancia=False)
    b = experimento.validacao_aninhada("gradient_boosting", X, y, g, n_externo=3,
                                       n_interno=2, importancia=False)
    assert a["resumo"] == b["resumo"]
    assert np.array_equal(a["oof_proba"], b["oof_proba"])


def test_oof_cobre_todos():
    X, y, g = _amostra()
    res = experimento.validacao_aninhada("logistica", X, y, g, n_externo=3, n_interno=2)
    assert (res["fold_id"] >= 0).all()
    assert len(res["folds"]) == 3
    assert set(res["folds"][0]["importancia"]) == set(config.ATRIBUTOS)
    assert 0 < res["folds"][0]["limiar_triagem"] < 1
