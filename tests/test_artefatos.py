import re

import pytest

import artefatos
import config


def test_numero_ptbr():
    assert artefatos.numero(0.77041) == "0{,}770"
    assert artefatos.numero(0.77041, 2) == "0{,}77"
    assert artefatos.inteiro(11454) == "11{.}454"
    assert artefatos.inteiro(168) == "168"
    assert artefatos.pct(42.64) == "42{,}6\\%"
    # Sinal de menos tipográfico, não hífen.
    assert artefatos.numero(-0.0119) == "$-$0{,}012"


def test_chave_sem_espaco_nem_acento():
    assert artefatos.chave("auc", "HDA 1") == "auc-hda1"
    assert artefatos.chave("prev", "Sistólico e diastólico") == "prev-sistolicoediastolico"


def _gerado():
    if not (config.RESULTADOS / "interpretacao.json").exists():
        pytest.skip("resultados ainda não gerados")
    artefatos.gerar(config.RESULTADOS, config.RELATORIO)
    return (config.RELATORIO / "numeros.tex").read_text(encoding="utf-8")


def test_numeros_formato_ptbr():
    texto = _gerado()
    valores = re.findall(r"\\defnum\{[^}]+\}\{(.*)\}$", texto, flags=re.M)
    assert valores
    assert not [v for v in valores if re.search(r"\d\.\d", v)]


def test_tabelas_geradas():
    _gerado()
    for nome in ("tab_metricas", "tab_hiperparametros", "tab_testes"):
        caminho = config.RELATORIO / "tabelas" / f"{nome}.tex"
        assert caminho.exists() and "\\begin{tabular" in caminho.read_text(encoding="utf-8")


def test_tabela_de_testes_cabe_numa_coluna():
    _gerado()
    texto = (config.RELATORIO / "tabelas" / "tab_testes.tex").read_text(encoding="utf-8")
    # Siglas no lugar dos nomes completos (explicadas na legenda).
    assert "LR $\\times$ RF" in texto and "Regressão Logística" not in texto


def test_moda_por_parametro():
    folds = [{"params": {"a": 1, "b": "x"}}, {"params": {"a": 1, "b": "y"}},
             {"params": {"a": 2, "b": "y"}}]
    assert artefatos.moda_por_parametro(folds) == {"a": (1, 2), "b": ("y", 2)}


def test_negrito_em_empates():
    # 0,8991 e 0,8993 aparecem iguais (0,899) na tabela: os dois ficam em negrito.
    assert artefatos.melhores({"lr": 0.8991, "gb": 0.8993, "rf": 0.8980}) == {"lr", "gb"}
