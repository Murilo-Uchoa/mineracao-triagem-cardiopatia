from functools import lru_cache

import pytest

import auditoria
import base_dados
import config


@lru_cache(maxsize=1)
def _eda():
    X, y, grupos, base = base_dados.carregar_base(config.RAW)
    return auditoria.rodar(base, X, y, grupos, destino=None)


def test_oner_sopro():
    assert round(_eda()["sopro"]["oner"]["acuracia"], 3) == 0.921


def test_retornos():
    r = _eda()["retornos"]
    assert r["pares_consecutivos"] == 168
    assert r["esperado_ao_acaso"] == pytest.approx(2.1, abs=0.2)


def test_auc_sopro_maior_que_todos():
    auc = _eda()["auc_univariada"]
    mantidos = [auc[c]["auc"] for c in config.ATRIBUTOS]
    assert auc["SOPRO"]["auc"] > max(mantidos)
    assert set(auc) == set(config.ATRIBUTOS + config.VAZAMENTO)


def test_tamanho_bruto():
    assert _eda()["n_bruto"] == 12873


def test_convenio_antes_e_depois():
    c = _eda()["convenio"]
    assert c["categorias_depois"] < c["categorias_antes"]


def test_pulsos_e_periodo():
    e = _eda()
    assert e["pulsos"]["prevalencia"]["Femorais diminuídos"]["n"] == 38
    assert e["periodo"]["sem_data"] == 153
    assert 99.0 < e["periodo"]["pct_2003_2010"] < 100.0
