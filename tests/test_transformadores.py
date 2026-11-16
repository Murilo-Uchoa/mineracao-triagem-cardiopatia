from functools import lru_cache

import numpy as np
import pandas as pd

import base_dados
import config
import transformadores as tr


@lru_cache(maxsize=1)
def _X():
    X, _, _, _ = base_dados.carregar_base(config.RAW)
    return X


def test_imputador_usa_so_treino():
    X = _X()
    imp = tr.ImputadorEstratificado(config.NUMERICAS).fit(X.iloc[:100])
    assert imp.mediana_global_["Peso"] == X["Peso"].iloc[:100].median()
    assert imp.mediana_global_["Peso"] != X["Peso"].median()


def test_imputador_estrato_vazio_cai_na_global():
    treino = pd.DataFrame({
        "Peso": [4.0, 5.0, 30.0, np.nan],
        "IDADE": [0.5, 1.0, 10.0, 1.5],
        "SEXO": ["F", "F", "M", "F"],
    })
    imp = tr.ImputadorEstratificado(["Peso", "IDADE"]).fit(treino)
    novo = pd.DataFrame({"Peso": [np.nan], "IDADE": [15.0], "SEXO": [np.nan]})
    saida = imp.transform(novo)
    # Estrato (Não informado, Adolescente) não existe no treino: mediana global.
    assert saida[0, 0] == np.median([4.0, 5.0, 30.0])


def test_imputador_usa_estrato_quando_existe():
    treino = pd.DataFrame({
        "Peso": [4.0, 6.0, 30.0, 40.0, np.nan],
        "IDADE": [0.5, 1.0, 10.0, 11.0, 1.2],
        "SEXO": ["F", "F", "M", "M", "F"],
    })
    imp = tr.ImputadorEstratificado(["Peso", "IDADE"]).fit(treino)
    saida = imp.transform(treino)
    assert saida[4, 0] == 5.0  # mediana das lactentes F, não a global (18.0)


def test_sem_nan_apos_transform():
    X = _X()
    matriz = tr.montar_preprocessador().fit_transform(X)
    assert np.isnan(matriz).sum() == 0


def test_categoria_nova_nao_quebra():
    X = _X()
    treino = X[(X["PULSOS"] != "Diminuídos") & (X["Convenio"] != "SUS")]
    novo = X[(X["PULSOS"] == "Diminuídos")].head(1).copy()
    novo["Convenio"] = "SUS"
    prep = tr.montar_preprocessador().fit(treino)
    assert prep.transform(novo).shape[0] == 1

    cod = tr.CodificadorFrequencia().fit(treino[["Convenio"]])
    assert cod.transform(novo[["Convenio"]])[0, 0] == 0.0


def test_codificador_frequencia_conta_no_treino():
    treino = pd.DataFrame({"Convenio": ["A", "A", "B", np.nan]})
    cod = tr.CodificadorFrequencia().fit(treino)
    saida = cod.transform(pd.DataFrame({"Convenio": ["A", "B", np.nan, "Z"]}))
    assert saida[:, 0].tolist() == [0.5, 0.25, 0.25, 0.0]


def test_indicadores_de_ausencia():
    X = _X()
    imp = tr.ImputadorEstratificado(config.NUMERICAS).fit(X)
    nomes = list(imp.get_feature_names_out())
    assert "Altura_ausente" in nomes
    saida = imp.transform(X)
    assert saida[:, nomes.index("Altura_ausente")].sum() == X["Altura"].isna().sum()
