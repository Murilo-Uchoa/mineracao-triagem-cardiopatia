"""Regressões de redação apontadas na revisão final do artigo."""

import re

import config

TEX = (config.RELATORIO / "main.tex").read_text(encoding="utf-8")


def test_nao_alega_erro_irredutivel():
    assert "erro irredutível" not in TEX


def test_nao_alega_equivalencia_sem_teste_de_equivalencia():
    assert "equivalente" not in TEX and "não diferem entre si" not in TEX


def test_declaracao_nao_promete_todo_numero():
    assert "todo número do texto" not in TEX


def test_pulsos_justificado_no_texto():
    assert re.search(r"PULSOS[^.]*palpação", TEX)


def test_faixa_de_n_nao_atribuida_a_kohavi():
    # A linha inteira: o ponto de "1.000" cortaria a frase antes da citação.
    linha = next(l for l in TEX.splitlines() if "1.000 < N" in l)
    trecho = linha[linha.index("1.000 < N"):].split("Usamos")[0]
    assert "kohavi" not in trecho


def test_justifica_zscore_e_onehot():
    assert re.search(r"z-score[^.]*escala", TEX)
    assert re.search(r"one-hot[^.]*nominais|nominais[^.]*one-hot", TEX)


def test_sopro_nao_e_literalmente_o_diagnostico():
    assert "O sopro não é preditor do diagnóstico: é o diagnóstico" not in TEX
