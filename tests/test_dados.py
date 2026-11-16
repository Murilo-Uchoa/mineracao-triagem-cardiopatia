from functools import lru_cache

import numpy as np
import pandas as pd

import config
import base_dados as dados


@lru_cache(maxsize=1)
def _base():
    return dados.carregar_base(config.RAW)


def test_X_tem_so_os_13_atributos():
    X, _, _, _ = _base()
    assert list(X.columns) == config.ATRIBUTOS
    assert X["PA_medida"].isin([0, 1]).all()


def test_y():
    _, y, _, _ = _base()
    assert len(y) == 11454
    assert round(y.mean(), 3) == 0.426


def test_base_alinhada_com_X():
    X, y, grupos, base = _base()
    assert len(base) == len(X) == len(grupos)
    assert (base.index == X.index).all()
    assert {"SOPRO", "B2", "ID", "DN"} <= set(base.columns)
    # ID numérico: ordenado como texto, "10" viria antes de "2".
    assert pd.api.types.is_integer_dtype(base["ID"])


def test_convenio_unifica_variantes():
    s = pd.Series(["Medial", "MEDIAL", "NORCLIN.", "Norclínicas", np.nan, " Sul  America "])
    esperado = ["MEDIAL", "MEDIAL", "NORCLIN", "NORCLINICAS", np.nan, "SUL AMERICA"]
    assert dados.padronizar_convenio(s).tolist()[:4] == esperado[:4]
    assert pd.isna(dados.padronizar_convenio(s).iloc[4])
    assert dados.padronizar_convenio(s).iloc[5] == "SUL AMERICA"


def test_chave_paciente():
    df = pd.DataFrame({
        "ID": [1, 2, 3, 4],
        "DN": pd.to_datetime(["2004-05-05", "2004-05-05", None, None]),
        "SEXO": ["F", "F", "F", "F"],
    })
    chave = dados.chave_paciente(df)
    assert chave[0] == chave[1]
    assert chave[2] != chave[3]
    assert chave[2] not in chave[:2] and chave[3] not in chave[:2]


def test_retornos():
    _, _, grupos, base = _base()
    ordem = np.argsort(base["ID"].to_numpy())
    g = grupos[ordem]
    assert int((g[1:] == g[:-1]).sum()) == 168
