"""Transformações com parâmetro, ajustadas só no treino de cada partição.

São as transformações que a A1 propôs e deixou para a A2 justamente por terem
parâmetros estimados a partir dos dados — medianas, médias, desvios,
frequências, categorias. Dentro de um `Pipeline`, o `fit` vê apenas o treino
da partição e o `transform` só aplica ao teste o que foi aprendido.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import config

# Faixas da pediatria usadas na A1 (lactente, pré-escolar, escolar, adolescente).
FAIXAS = [-0.01, 2, 6, 12, 19]
ROTULOS_FAIXA = ["Lactente", "Pré-escolar", "Escolar", "Adolescente"]


class ImputadorEstratificado(BaseEstimator, TransformerMixin):
    """Mediana estratificada por sexo e faixa etária, como na A1.

    A idade é imputada primeiro, pela mediana global do treino, porque é ela
    que define a faixa etária do estrato. Para as demais colunas, vale a
    mediana do estrato (sexo × faixa) e, se o estrato não existir no treino
    ou não tiver valor observado, a mediana global do treino.

    Acrescenta um indicador `<coluna>_ausente` para cada coluna que tinha
    ausência no treino: a A1 mostrou que a ausência carrega informação
    (PA_medida), e a imputação sozinha a apagaria.
    """

    def __init__(self, colunas, col_sexo="SEXO", col_idade="IDADE"):
        self.colunas = colunas
        self.col_sexo = col_sexo
        self.col_idade = col_idade

    def _estrato(self, X):
        idade = X[self.col_idade].fillna(self.mediana_global_[self.col_idade])
        faixa = pd.cut(idade, bins=FAIXAS, labels=ROTULOS_FAIXA).astype(object)
        sexo = X[self.col_sexo].astype(object).where(X[self.col_sexo].notna(),
                                                      config.NAO_INFORMADO)
        return sexo.astype(str) + "|" + faixa.astype(str)

    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        self.mediana_global_ = {c: float(X[c].median()) for c in self.colunas}
        estrato = self._estrato(X)
        self.mediana_estrato_ = {
            c: X[c].groupby(estrato).median().dropna().to_dict()
            for c in self.colunas if c != self.col_idade
        }
        self.com_ausencia_ = [c for c in self.colunas if X[c].isna().any()]
        return self

    def transform(self, X):
        X = pd.DataFrame(X)
        estrato = self._estrato(X)
        saida = []
        for c in self.colunas:
            valor = X[c].astype("float64")
            if c != self.col_idade:
                valor = valor.fillna(estrato.map(self.mediana_estrato_[c]))
            saida.append(valor.fillna(self.mediana_global_[c]).to_numpy())
        for c in self.com_ausencia_:
            saida.append(X[c].isna().astype("float64").to_numpy())
        return np.column_stack(saida)

    def get_feature_names_out(self, input_features=None):
        return np.array(list(self.colunas) + [f"{c}_ausente" for c in self.com_ausencia_],
                        dtype=object)


class CodificadorFrequencia(BaseEstimator, TransformerMixin):
    """Troca cada categoria pela sua frequência relativa no treino.

    É a codificação que a A1 escolheu para o Convenio (228 categorias depois
    da padronização): o one-hot criaria centenas de colunas esparsas, e o
    target encoding usaria o próprio alvo, com risco de vazamento. Ausente
    conta como a categoria "Não informado"; categoria nunca vista no treino
    recebe frequência 0.
    """

    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        self.colunas_ = list(X.columns)
        self.frequencias_ = {
            c: self._rotulos(X[c]).value_counts(normalize=True).to_dict()
            for c in self.colunas_
        }
        return self

    @staticmethod
    def _rotulos(serie):
        return serie.astype(object).where(serie.notna(), config.NAO_INFORMADO)

    def transform(self, X):
        X = pd.DataFrame(X)
        return np.column_stack([
            self._rotulos(X[c]).map(self.frequencias_[c]).fillna(0.0).astype("float64")
            for c in self.colunas_
        ])

    def get_feature_names_out(self, input_features=None):
        return np.array([f"{c}_freq" for c in self.colunas_], dtype=object)


def montar_preprocessador() -> ColumnTransformer:
    """As transformações da A2 num só objeto, para viver dentro do Pipeline."""
    numericas = Pipeline([
        ("imputacao", ImputadorEstratificado(config.NUMERICAS)),
        ("zscore", StandardScaler()),
    ])
    categoricas = Pipeline([
        ("imputacao", SimpleImputer(strategy="constant", fill_value=config.NAO_INFORMADO)),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    convenio = Pipeline([
        ("frequencia", CodificadorFrequencia()),
        ("zscore", StandardScaler()),
    ])
    return ColumnTransformer([
        # SEXO entra no ramo numérico só como estrato da imputação.
        ("num", numericas, config.NUMERICAS + ["SEXO"]),
        ("cat", categoricas, config.CATEGORICAS),
        ("bin", "passthrough", config.BINARIAS),
        ("conv", convenio, [config.CONVENIO]),
    ])
