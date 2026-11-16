"""Métricas de avaliação e limiar de triagem.

Segue a convenção dos slides de experimentação: classe positiva = Anormal e
regra de decisão "Score > Limiar ⇒ classe = Positiva".
"""

from __future__ import annotations

import math

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def calcular_metricas(y, proba, limiar: float = 0.5) -> dict[str, float]:
    """Métricas dependentes do limiar e as duas áreas sob curva.

    AUC-ROC e AUC-PR não dependem do limiar; a AUC-PR é calculada como
    precisão média (average precision), a forma usual de resumir a curva PR.
    """
    y = np.asarray(y).astype(int)
    proba = np.asarray(proba, dtype=float)
    pred = (proba > limiar).astype(int)

    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())

    def razao(a, b):
        return a / b if b else 0.0

    sens = razao(tp, tp + fn)
    espec = razao(tn, tn + fp)
    prec = razao(tp, tp + fp)
    return {
        "auc_roc": float(roc_auc_score(y, proba)),
        "auc_pr": float(average_precision_score(y, proba)),
        "acuracia": razao(tp + tn, len(y)),
        "acuracia_balanceada": (sens + espec) / 2,
        "sensibilidade": sens,
        "especificidade": espec,
        "precisao": prec,
        "f1": razao(2 * prec * sens, prec + sens),
    }


def limiar_para_sensibilidade(y, proba, alvo: float = 0.90) -> float:
    """Maior limiar cuja aplicação ("> limiar") atinge a sensibilidade alvo.

    Com k = ⌈alvo × positivos⌉, o limiar fica imediatamente abaixo do k-ésimo
    maior score entre os positivos, de modo que esse positivo — e todos os de
    score maior ou igual, inclusive empatados — passem a ser classificados
    como positivos.
    """
    y = np.asarray(y).astype(int)
    proba = np.asarray(proba, dtype=float)
    positivos = np.sort(proba[y == 1])[::-1]
    k = math.ceil(alvo * len(positivos))
    return float(np.nextafter(positivos[k - 1], -np.inf))
