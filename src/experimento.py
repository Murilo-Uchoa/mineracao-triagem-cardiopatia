"""Validação cruzada aninhada, estratificada e agrupada por paciente.

Laço externo (10 partições) estima o desempenho; laço interno (5 partições),
dentro de cada treino externo, escolhe os hiperparâmetros pela AUC-ROC. As
duas partições usam `StratifiedGroupKFold`: os atendimentos de uma mesma
criança ficam inteiros no treino ou no teste — a regra de ouro do
agrupamento por indivíduo.

Em cada partição externa também se escolhe o limiar de triagem (sensibilidade
≥ 0,90) com previsões fora da dobra do próprio treino, e se mede a
importância dos atributos por permutação no teste.
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold, cross_val_predict

import config
import modelos
from metricas import calcular_metricas, limiar_para_sensibilidade


def particoes(y, grupos, n, seed):
    """Partições estratificadas e agrupadas; as mesmas para todos os modelos."""
    separador = StratifiedGroupKFold(n_splits=n, shuffle=True, random_state=seed)
    return list(separador.split(np.zeros(len(y)), y, grupos))


def _separador_interno(n, seed):
    return StratifiedGroupKFold(n_splits=n, shuffle=True, random_state=seed)


def ajustar(nome, X, y, grupos, n_interno=config.N_INTERNO, seed=config.SEED):
    """Ajusta o pipeline no treino, com busca em grade quando há grade."""
    pipeline = modelos.montar_pipeline(nome)
    grade = modelos.GRADES[nome]
    if not grade:
        return pipeline.fit(X, y), {}
    busca = GridSearchCV(pipeline, grade, cv=_separador_interno(n_interno, seed),
                         scoring="roc_auc", n_jobs=-1, refit=True)
    busca.fit(X, y, groups=grupos)
    return busca.best_estimator_, _jsonavel(busca.best_params_)


def _jsonavel(params):
    saida = {}
    for chave, valor in params.items():
        if isinstance(valor, np.generic):
            valor = valor.item()
        saida[chave.replace("modelo__", "")] = valor
    return saida


def _resumir(lista):
    """Média e desvio-padrão amostral de cada métrica entre as partições."""
    chaves = lista[0].keys()
    return {c: {"media": float(np.mean([m[c] for m in lista])),
                "dp": float(np.std([m[c] for m in lista], ddof=1))} for c in chaves}


def validacao_aninhada(nome, X, y, grupos, n_externo=config.N_EXTERNO,
                       n_interno=config.N_INTERNO, seed=config.SEED,
                       registrar_particoes=False, importancia=True):
    y = np.asarray(y)
    grupos = np.asarray(grupos)
    oof = np.full(len(y), np.nan)
    fold_id = np.full(len(y), -1)
    folds, sobreposicoes = [], []

    for k, (tr, te) in enumerate(particoes(y, grupos, n_externo, seed)):
        X_tr, X_te = X.iloc[tr], X.iloc[te]
        y_tr, y_te, g_tr = y[tr], y[te], grupos[tr]

        modelo, params = ajustar(nome, X_tr, y_tr, g_tr, n_interno, seed)
        proba = modelo.predict_proba(X_te)[:, 1]
        oof[te] = proba
        fold_id[te] = k

        # Limiar de triagem escolhido sem ver o teste: previsões fora da dobra
        # do treino externo, com o mesmo separador agrupado do laço interno.
        proba_interna = cross_val_predict(
            clone(modelo), X_tr, y_tr, groups=g_tr,
            cv=_separador_interno(n_interno, seed), method="predict_proba", n_jobs=-1,
        )[:, 1]
        limiar = limiar_para_sensibilidade(y_tr, proba_interna, config.SENSIBILIDADE_TRIAGEM)

        registro = {
            "fold": k,
            "n_teste": int(len(te)),
            "params": params,
            "metricas_05": calcular_metricas(y_te, proba, 0.5),
            "limiar_triagem": limiar,
            "metricas_triagem": calcular_metricas(y_te, proba, limiar),
        }
        if importancia:
            perm = permutation_importance(modelo, X_te, y_te, scoring="roc_auc",
                                          n_repeats=10, random_state=seed, n_jobs=-1)
            registro["importancia"] = {c: float(v) for c, v in
                                       zip(X.columns, perm.importances_mean)}
        folds.append(registro)

        if registrar_particoes:
            for a, b in _separador_interno(n_interno, seed).split(X_tr, y_tr, g_tr):
                sobreposicoes.append(len(set(g_tr[a]) & set(g_tr[b])))

    resultado = {
        "modelo": nome,
        "folds": folds,
        "resumo": {"limiar_05": _resumir([f["metricas_05"] for f in folds]),
                   "triagem": _resumir([f["metricas_triagem"] for f in folds])},
        "oof_proba": oof,
        "fold_id": fold_id,
    }
    if registrar_particoes:
        resultado["sobreposicoes_internas"] = sobreposicoes
    return resultado


def rodar_todos(X, y, grupos, base, destino=config.RESULTADOS):
    """Roda a validação aninhada de todos os modelos e grava os resultados.

    As previsões por paciente vão para `previsoes_oof.csv`, que fica fora do
    repositório público (ID + diagnóstico); os JSONs só têm agregados.
    """
    destino.mkdir(parents=True, exist_ok=True)
    previsoes = pd.DataFrame({"ID": base["ID"].to_numpy(), "y": y})
    for nome in modelos.NOMES:
        inicio = time.time()
        res = validacao_aninhada(nome, X, y, grupos)
        previsoes["fold"] = res["fold_id"]
        previsoes[f"proba_{nome}"] = res["oof_proba"]
        saida = {k: v for k, v in res.items() if k not in ("oof_proba", "fold_id")}
        saida["segundos"] = round(time.time() - inicio, 1)
        (destino / f"aninhada_{nome}.json").write_text(
            json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{nome}: AUC {res['resumo']['limiar_05']['auc_roc']['media']:.3f} "
              f"({saida['segundos']} s)", flush=True)
    previsoes.to_csv(destino / "previsoes_oof.csv", index=False)
