import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

import metricas

# Exemplo dos slides do professor ("Limiar de decisão do modelo").
CLASSES = np.array([1, 0, 1, 0, 1, 0, 0, 1, 0, 0])
SCORES = np.array([.95, .93, .90, .65, .60, .55, .49, .45, .43, .25])


def test_exemplo_dos_slides_limiar_05():
    m = metricas.calcular_metricas(CLASSES, SCORES, limiar=0.5)
    # TP 3, FP 3, TN 3, FN 1, como na linha do slide para o limiar 0,5.
    assert m["sensibilidade"] == pytest.approx(0.75)
    assert m["especificidade"] == pytest.approx(0.5)
    assert m["precisao"] == pytest.approx(0.5)
    assert m["acuracia"] == pytest.approx(0.6)
    assert m["acuracia_balanceada"] == pytest.approx(0.625)
    assert m["f1"] == pytest.approx(2 * 0.5 * 0.75 / 1.25)


def test_limiar_usa_maior_estrito():
    # Score igual ao limiar é negativo: "Score > Limiar ⇒ classe = Positiva".
    m = metricas.calcular_metricas(np.array([1, 0]), np.array([0.5, 0.2]), limiar=0.5)
    assert m["sensibilidade"] == 0.0


def test_auc_roc_exemplo():
    m = metricas.calcular_metricas(CLASSES, SCORES)
    assert m["auc_roc"] == pytest.approx(roc_auc_score(CLASSES, SCORES))


def test_limiar_triagem_exemplo():
    limiar = metricas.limiar_para_sensibilidade(CLASSES, SCORES, alvo=0.90)
    assert limiar < 0.45
    assert metricas.calcular_metricas(CLASSES, SCORES, limiar)["sensibilidade"] == 1.0


def test_limiar_com_empates():
    y = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0])
    s = np.array([.9, .8, .8, .8, .7, .7, .7, .6, .6, .6, .6, .6, .1])
    limiar = metricas.limiar_para_sensibilidade(y, s, alvo=0.90)
    assert metricas.calcular_metricas(y, s, limiar)["sensibilidade"] >= 0.90
