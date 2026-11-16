"""Base de modelagem da A2: atributos, alvo e chave de paciente.

Parte do dado bruto, aplica a limpeza da A1 sem a imputação e devolve:

* `X` com os 13 atributos do modelo (SOPRO e B2 ficam de fora: vazamento);
* `y` binário, com Anormal = 1;
* `grupos`, a chave de paciente usada na partição agrupada — o ID identifica o
  atendimento, não a criança, e a base tem retornos;
* `base`, o DataFrame limpo completo, só para a EDA e a interpretação.
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

import config
import limpeza


def padronizar_convenio(serie: pd.Series) -> pd.Series:
    """Unifica caixa, acento e pontuação do convênio.

    Inconsistência léxica que a A1 não tratou: "Medial" e "MEDIAL",
    "Semepe" e "SEMEPE", "NORCLIN." e "NORCLIN". Abreviações diferentes
    ("SA", "SULA", "Sul America") não são fundidas: não há como saber, só
    pelo texto, que se referem ao mesmo convênio.
    """
    def norma(valor):
        if not isinstance(valor, str):
            return np.nan
        sem_acento = "".join(
            c for c in unicodedata.normalize("NFKD", valor)
            if not unicodedata.combining(c)
        )
        texto = re.sub(r"[^\w\s]", "", sem_acento.upper())
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto or np.nan

    return serie.map(norma)


def chave_paciente(df: pd.DataFrame) -> np.ndarray:
    """Chave aproximada da criança: data de nascimento + sexo.

    Sem data de nascimento não há como ligar atendimentos, e a linha vira um
    grupo só dela. A chave junta também crianças distintas nascidas no mesmo
    dia, o que deixa a validação mais rígida, nunca mais frouxa.
    """
    sexo = df["SEXO"].astype(object).where(df["SEXO"].notna(), config.NAO_INFORMADO)
    dn = pd.to_datetime(df["DN"], errors="coerce")
    com_dn = dn.dt.strftime("%Y-%m-%d") + "|" + sexo.astype(str)
    sem_dn = "sem_dn|" + df["ID"].astype(str)
    return np.where(dn.notna(), com_dn, sem_dn).astype(str)


def carregar_base(caminho_raw=config.RAW):
    """Devolve `X`, `y`, `grupos` e a base limpa completa, alinhados."""
    df, _ = limpeza.limpar(str(caminho_raw), imputar=False)
    df = df.reset_index(drop=True)
    # O bruto é lido todo como texto; o ID volta a ser número para ordenar.
    df["ID"] = pd.to_numeric(df["ID"], errors="raise").astype("int64")
    df["Convenio_original"] = df[config.CONVENIO]
    df[config.CONVENIO] = padronizar_convenio(df[config.CONVENIO])

    X = df[config.ATRIBUTOS].copy()
    X["PA_medida"] = X["PA_medida"].astype(int)
    for col in config.CATEGORICAS + [config.CONVENIO]:
        # object com np.nan: o formato que os transformadores do sklearn esperam.
        X[col] = X[col].astype(object).where(X[col].notna(), np.nan)
    for col in config.NUMERICAS:
        X[col] = X[col].astype("float64")

    y = (df[config.ALVO] == config.POSITIVO).astype(int).to_numpy()
    grupos = chave_paciente(df)
    return X, y, grupos, df
