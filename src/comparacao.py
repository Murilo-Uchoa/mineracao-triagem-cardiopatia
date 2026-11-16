"""Comparação estatística entre modelos num único dataset.

Segue os slides de comparação de modelos (Dietterich, 1998): o 5×2-fold CV
t-test, que controla melhor o erro Tipo I que o teste t sobre as partições de
uma validação cruzada comum. Como são três pares comparados, os valores-p são
corrigidos pelo procedimento de Holm.

Cada uma das 10 execuções repete o algoritmo inteiro — inclusive a busca de
hiperparâmetros no laço interno —, com metades formadas por grupos de
paciente.
"""

from __future__ import annotations

import itertools
import json

import numpy as np
from scipy import stats

import config
from experimento import ajustar, particoes
from metricas import calcular_metricas


def estatistica_5x2cv(dif) -> tuple[float, float]:
    """t̃ de Dietterich e o valor-p bilateral (t de Student com 5 g.l.).

    `dif[i, j]` é a diferença de desempenho entre os dois modelos na
    replicação i, metade j. O numerador é a diferença da primeira replicação
    na primeira metade, e não a média das dez.
    """
    dif = np.asarray(dif, dtype=float)
    media = dif.mean(axis=1, keepdims=True)
    s2 = ((dif - media) ** 2).sum(axis=1)
    t = dif[0, 0] / np.sqrt(s2.mean())
    return float(t), float(2 * stats.t.sf(abs(t), df=5))


def holm(pvalores) -> list[float]:
    """Valores-p ajustados por Holm, na ordem original."""
    p = np.asarray(pvalores, dtype=float)
    m = len(p)
    ordem = np.argsort(p)
    ajustado = np.empty(m)
    acumulado = 0.0
    for posicao, i in enumerate(ordem):
        acumulado = max(acumulado, (m - posicao) * p[i])
        ajustado[i] = min(acumulado, 1.0)
    return ajustado.tolist()


def rodar_5x2cv(X, y, grupos, nomes=("logistica", "random_forest", "gradient_boosting"),
                seeds=config.SEEDS_5X2, destino=config.RESULTADOS):
    y = np.asarray(y)
    grupos = np.asarray(grupos)
    medidas = {n: {"auc_roc": np.zeros((5, 2)), "erro": np.zeros((5, 2))} for n in nomes}

    for i, seed in enumerate(seeds):
        for j, (tr, te) in enumerate(particoes(y, grupos, 2, seed)):
            for nome in nomes:
                modelo, _ = ajustar(nome, X.iloc[tr], y[tr], grupos[tr], seed=seed)
                proba = modelo.predict_proba(X.iloc[te])[:, 1]
                m = calcular_metricas(y[te], proba, 0.5)
                medidas[nome]["auc_roc"][i, j] = m["auc_roc"]
                medidas[nome]["erro"][i, j] = 1 - m["acuracia"]
            print(f"replicação {i + 1}, metade {j + 1} concluída", flush=True)

    pares = []
    for a, b in itertools.combinations(nomes, 2):
        par = {"a": a, "b": b}
        for metrica in ("auc_roc", "erro"):
            dif = medidas[a][metrica] - medidas[b][metrica]
            t, p = estatistica_5x2cv(dif)
            par[metrica] = {"t": t, "p": p, "dif_media": float(dif.mean())}
        pares.append(par)
    for metrica in ("auc_roc", "erro"):
        for par, p_ajustado in zip(pares, holm([par[metrica]["p"] for par in pares])):
            par[metrica]["p_holm"] = p_ajustado

    saida = {
        "seeds": list(seeds),
        "medidas": {n: {k: v.tolist() for k, v in d.items()} for n, d in medidas.items()},
        "pares": pares,
    }
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "comparacao_5x2cv.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida
