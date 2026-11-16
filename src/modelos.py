"""Algoritmos comparados e espaços de busca de hiperparâmetros.

* `dummy` — piso de referência: prevê sempre a prevalência do treino.
* `logistica` — baseline simples: regressão logística com regularização L2.
* `random_forest` e `gradient_boosting` — modelos mais complexos, de árvores.

Cada modelo é um `Pipeline` (pré-processamento + estimador): a busca de
hiperparâmetros e a validação ajustam as transformações junto com o modelo,
sempre só no treino.
"""

from __future__ import annotations

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

import config
from transformadores import montar_preprocessador

NOMES = ["dummy", "logistica", "random_forest", "gradient_boosting"]

ROTULOS = {
    "dummy": "Classe majoritária",
    "logistica": "Regressão Logística",
    "random_forest": "Random Forest",
    "gradient_boosting": "Gradient Boosting",
}

GRADES = {
    "dummy": {},
    "logistica": {
        "modelo__C": [0.01, 0.1, 1, 10],
        "modelo__class_weight": [None, "balanced"],
    },
    "random_forest": {
        "modelo__max_depth": [None, 8, 16],
        "modelo__min_samples_leaf": [1, 5, 20],
        "modelo__class_weight": [None, "balanced"],
    },
    "gradient_boosting": {
        "modelo__learning_rate": [0.05, 0.1],
        "modelo__max_leaf_nodes": [15, 31],
        "modelo__l2_regularization": [0.0, 1.0],
        "modelo__class_weight": [None, "balanced"],
    },
}


def _estimador(nome):
    if nome == "dummy":
        return DummyClassifier(strategy="prior")
    if nome == "logistica":
        return LogisticRegression(max_iter=2000, random_state=config.SEED)
    if nome == "random_forest":
        return RandomForestClassifier(n_estimators=300, n_jobs=1,
                                      random_state=config.SEED)
    if nome == "gradient_boosting":
        # Early stopping explícito: o padrão "auto" só o liga acima de 10 mil
        # linhas, o que mudaria o modelo entre o laço interno e o externo.
        return HistGradientBoostingClassifier(
            max_iter=300, early_stopping=True, validation_fraction=0.1,
            n_iter_no_change=10, random_state=config.SEED,
        )
    raise ValueError(f"modelo desconhecido: {nome}")


def montar_pipeline(nome: str) -> Pipeline:
    return Pipeline([("prep", montar_preprocessador()), ("modelo", _estimador(nome))])
