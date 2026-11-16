import numpy as np
import pytest
from scipy import stats

import comparacao


def test_formula_5x2cv():
    dif = np.array([[.02, 0], [.01, .01], [.03, .01], [0, .02], [.02, .02]])
    t, p = comparacao.estatistica_5x2cv(dif)
    assert t == pytest.approx(1.8257, abs=1e-3)
    assert p == pytest.approx(2 * stats.t.sf(1.8257418583505538, 5))


def test_formula_usa_so_a_primeira_diferenca_no_numerador():
    dif = np.array([[.02, 0], [.01, .01], [.03, .01], [0, .02], [.02, .02]])
    outra = dif.copy()
    outra[4, 1] = 0.05   # muda a variância, não o numerador
    outra[4, 0] = -0.01
    t1, _ = comparacao.estatistica_5x2cv(dif)
    t2, _ = comparacao.estatistica_5x2cv(outra)
    assert np.sign(t1) == np.sign(t2) and t1 != t2


def test_holm():
    assert comparacao.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_holm_limita_em_1():
    assert comparacao.holm([0.6, 0.7]) == pytest.approx([1.0, 1.0])
