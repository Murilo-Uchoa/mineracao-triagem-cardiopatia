"""Interpretação dos resultados: erros, importância e sentido dos efeitos.

* Matrizes de confusão fora da dobra — cada paciente avaliado uma única vez —
  no limiar padrão (0,5) e no limiar de triagem escolhido em cada partição.
* Onde caem os falsos negativos: faixa etária, motivo do encaminhamento,
  aferição da pressão e presença de sopro (que o modelo não vê).
* Importância por permutação agregada entre as partições.
* Razões de chance da regressão logística, só para ler o sentido de cada
  efeito — nunca para avaliar desempenho.
"""

from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import config
import modelos
from auditoria import SOPRO_PRESENTE
from transformadores import FAIXAS, ROTULOS_FAIXA


def matriz_confusao(y, proba, limiar) -> dict[str, int]:
    y = np.asarray(y)
    pred = np.asarray(proba) > np.asarray(limiar)
    return {"tp": int((pred & (y == 1)).sum()), "fn": int((~pred & (y == 1)).sum()),
            "fp": int((pred & (y == 0)).sum()), "tn": int((~pred & (y == 0)).sum())}


def agregar_importancia(folds) -> dict[str, dict[str, float]]:
    tabela = pd.DataFrame([f["importancia"] for f in folds])
    agg = {c: {"media": float(tabela[c].mean()), "dp": float(tabela[c].std(ddof=1))}
           for c in tabela.columns}
    return dict(sorted(agg.items(), key=lambda kv: kv[1]["media"], reverse=True))


def taxa_fn_por_grupo(y, pred, grupo) -> dict[str, dict]:
    y = np.asarray(y)
    pred = np.asarray(pred).astype(bool)
    grupo = pd.Series(grupo).reset_index(drop=True)
    saida = {}
    for valor in grupo.dropna().unique():
        m = (grupo == valor).to_numpy() & (y == 1)
        fn = int((m & ~pred).sum())
        saida[str(valor)] = {"positivos": int(m.sum()), "fn": fn,
                             "taxa_fn": fn / int(m.sum()) if m.sum() else 0.0}
    return saida


def _carregar(resultados):
    aninhada = {n: json.loads((resultados / f"aninhada_{n}.json").read_text(encoding="utf-8"))
                for n in modelos.NOMES}
    previsoes = pd.read_csv(resultados / "previsoes_oof.csv")
    return aninhada, previsoes


def _razoes_de_chance(X, y, folds):
    """Logística reajustada na base inteira com os hiperparâmetros mais escolhidos."""
    mais_comum = Counter(json.dumps(f["params"], sort_keys=True) for f in folds)
    params = json.loads(mais_comum.most_common(1)[0][0])
    pipeline = modelos.montar_pipeline("logistica")
    pipeline.set_params(**{f"modelo__{k}": v for k, v in params.items()})
    pipeline.fit(X, y)
    nomes = pipeline.named_steps["prep"].get_feature_names_out()
    coef = pipeline.named_steps["modelo"].coef_[0]
    ordem = np.argsort(-np.abs(coef))
    return {"params": params,
            "coeficientes": {str(nomes[i]): {"coef": float(coef[i]),
                                             "razao_de_chance": float(np.exp(coef[i]))}
                             for i in ordem}}


def rodar(X, y, base, resultados=config.RESULTADOS, destino=config.RESULTADOS):
    y = np.asarray(y)
    aninhada, previsoes = _carregar(resultados)
    assert (previsoes["ID"].to_numpy() == base["ID"].to_numpy()).all()

    candidatos = [n for n in modelos.NOMES if n != "dummy"]
    melhor = max(candidatos,
                 key=lambda n: aninhada[n]["resumo"]["limiar_05"]["auc_roc"]["media"])
    proba = previsoes[f"proba_{melhor}"].to_numpy()
    limiar_fold = {f["fold"]: f["limiar_triagem"] for f in aninhada[melhor]["folds"]}
    limiar = previsoes["fold"].map(limiar_fold).to_numpy()

    faixa = pd.cut(base["IDADE"], bins=FAIXAS, labels=ROTULOS_FAIXA).astype(object)
    faixa = faixa.where(faixa.notna(), config.NAO_INFORMADO)
    pred_triagem = proba > limiar
    pred_05 = proba > 0.5
    sopro = base["SOPRO"].isin(SOPRO_PRESENTE).to_numpy()

    rotulo_sopro = pd.Series(np.where(sopro, "com sopro", "sem sopro"))

    def perfil(pred):
        fn = (y == 1) & ~pred
        return {
            # Entre os anormais, quanto o modelo perde com e sem sopro na ausculta.
            "sopro": taxa_fn_por_grupo(y, pred, rotulo_sopro),
            "faixa_etaria": taxa_fn_por_grupo(y, pred, faixa),
            "motivo1": taxa_fn_por_grupo(y, pred, base["MOTIVO1"].fillna(config.NAO_INFORMADO)),
            "pa_medida": taxa_fn_por_grupo(y, pred, base["PA_medida"].astype(str)),
            "pct_fn_com_sopro": float(sopro[fn].mean() * 100) if fn.any() else 0.0,
            "pct_positivos_com_sopro": float(sopro[y == 1].mean() * 100),
            "pct_fn_sem_sopro": float((~sopro[fn]).mean() * 100) if fn.any() else 0.0,
        }

    # Subanálise: sem os encaminhamentos de cardiopatia já estabelecida, positivos
    # "fáceis" para uma triagem (o diagnóstico prévio já é conhecido).
    resto = (base["MOTIVO1"] != "1 - Cardiopatia já estabelecida").fillna(True).to_numpy(bool)
    m_resto = matriz_confusao(y[resto], proba[resto], limiar[resto])
    subanalise = {
        "n": int(resto.sum()),
        "auc_roc": float(roc_auc_score(y[resto], proba[resto])),
        "auc_roc_todos": float(roc_auc_score(y, proba)),
        "sensibilidade_triagem": m_resto["tp"] / (m_resto["tp"] + m_resto["fn"]),
        "especificidade_triagem": m_resto["tn"] / (m_resto["tn"] + m_resto["fp"]),
    }

    saida = {
        "melhor": melhor,
        "sem_cardiopatia_estabelecida": subanalise,
        "matriz_05": matriz_confusao(y, proba, 0.5),
        "matriz_triagem": matriz_confusao(y, proba, limiar),
        "limiares_triagem": [limiar_fold[k] for k in sorted(limiar_fold)],
        "perfil_fn_05": perfil(pred_05),
        "perfil_fn_triagem": perfil(pred_triagem),
        "importancia": {n: agregar_importancia(aninhada[n]["folds"])
                        for n in dict.fromkeys([melhor, "logistica"])},
        "logistica": _razoes_de_chance(X, y, aninhada["logistica"]["folds"]),
    }
    if destino is not None:
        (destino / "interpretacao.json").write_text(
            json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida
