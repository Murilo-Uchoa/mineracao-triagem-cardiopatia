"""Números da análise exploratória e da auditoria de vazamento.

Tudo o que a seção "Dados e Análise Exploratória" do artigo cita sai daqui:
tamanho e balanceamento da base, a evidência do vazamento de SOPRO e B2, a
força de cada atributo isolado, os retornos do mesmo paciente e a deriva da
prevalência ao longo dos anos.

A AUC univariada é medida fora da amostra: nas categóricas, a taxa de
anormais por categoria é aprendida no treino de cada partição e aplicada ao
teste. Assim, o Convenio, com centenas de categorias, não ganha uma AUC
inflada por decorar a base.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import config
from experimento import particoes

SOPRO_PRESENTE = {"Sistólico", "Diastólico", "Contínuo", "Sistólico e diastólico"}


def _rotulos(serie):
    return serie.astype(object).where(serie.notna(), config.NAO_INFORMADO).astype(str)


def _auc_melhor_sentido(y, score):
    auc = roc_auc_score(y, score)
    return max(auc, 1 - auc)


def auc_univariada(serie, y, grupos):
    """AUC de um atributo sozinho, fora da amostra nas categóricas."""
    y = np.asarray(y)
    if pd.api.types.is_numeric_dtype(serie) and serie.nunique() > 2:
        observado = serie.notna().to_numpy()
        return {"auc": float(_auc_melhor_sentido(y[observado], serie[observado])),
                "cobertura": float(observado.mean())}
    rotulos = _rotulos(serie).to_numpy()
    score = np.empty(len(y))
    for tr, te in particoes(y, grupos, config.N_EXTERNO, config.SEED):
        taxa = pd.Series(y[tr]).groupby(rotulos[tr]).mean()
        score[te] = pd.Series(rotulos[te]).map(taxa).fillna(y[tr].mean()).to_numpy()
    return {"auc": float(_auc_melhor_sentido(y, score)), "cobertura": 1.0}


def _prevalencia(serie, y):
    tabela = pd.DataFrame({"cat": _rotulos(serie), "y": y}).groupby("cat")["y"]
    return {c: {"n": int(n), "pct_anormal": float(p * 100)}
            for c, n, p in zip(tabela.size().index, tabela.size(), tabela.mean())}


def _retornos(base, y, grupos):
    ordem = np.argsort(base["ID"].to_numpy())
    g = grupos[ordem]
    pares = int((g[1:] == g[:-1]).sum())

    com_dn = ~pd.Series(grupos).str.startswith("sem_dn").to_numpy()
    tamanhos = pd.Series(grupos[com_dn]).value_counts()
    p_coincidir = float(((tamanhos / com_dn.sum()) ** 2).sum())

    mesmo_dia = pd.DataFrame({"g": grupos, "dia": base["Atendimento"].astype(str), "y": y})
    mesmo_dia = mesmo_dia[com_dn].groupby(["g", "dia"])["y"].agg(["size", "nunique"])
    mesmo_dia = mesmo_dia[mesmo_dia["size"] >= 2]
    return {
        "pares_consecutivos": pares,
        "esperado_ao_acaso": p_coincidir * (len(g) - 1),
        "n_grupos": int(len(set(grupos))),
        "linhas_sem_dn": int((~com_dn).sum()),
        "grupos_com_dn": int(len(tamanhos)),
        "grupos_multiplos": int((tamanhos >= 2).sum()),
        "linhas_em_grupos_multiplos": int(tamanhos[tamanhos >= 2].sum()),
        "maior_grupo": int(tamanhos.max()),
        "grupos_mesmo_dia": int(len(mesmo_dia)),
        "mesmo_dia_alvo_divergente": int((mesmo_dia["nunique"] > 1).sum()),
    }


def rodar(base, X, y, grupos, destino=config.RESULTADOS):
    y = np.asarray(y)
    presente = base["SOPRO"].isin(SOPRO_PRESENTE).to_numpy()
    tp = int((presente & (y == 1)).sum())
    tn = int((~presente & (y == 0)).sum())

    # Colunas de texto do pandas comparam ausente como NA; vira False aqui.
    motivo2_sopro = (base["MOTIVO2"] == "6 - Sopro").fillna(False).astype(bool)
    sem_confirmacao = motivo2_sopro & (base["SOPRO"] == "Ausente").fillna(False).astype(bool)
    ano = pd.to_datetime(base["Atendimento"]).dt.year
    por_ano = pd.DataFrame({"ano": ano, "y": y}).dropna().groupby("ano")["y"].agg(["size", "mean"])
    por_ano = por_ano[por_ano["size"] >= 100]

    ordem = np.argsort(base["ID"].to_numpy())
    y_ordenado = y[ordem]
    p = y.mean()

    bruto = pd.read_csv(config.RAW, dtype=str)
    eda = {
        "n_bruto": int(len(bruto)),
        "n": int(len(y)),
        "n_anormal": int(y.sum()),
        "pct_anormal": float(y.mean() * 100),
        "atributos_brutos": int(bruto.shape[1]),
        "atributos_limpos": 20,
        "atributos_modelo": len(config.ATRIBUTOS),
        "ausencia_pct": {c: float(X[c].isna().mean() * 100) for c in config.ATRIBUTOS},
        "sopro": {
            "prevalencia": _prevalencia(base["SOPRO"], y),
            "oner": {"acuracia": float((tp + tn) / len(y)),
                     "sensibilidade": float(tp / (y == 1).sum()),
                     "especificidade": float(tn / (y == 0).sum())},
        },
        "b2": {"prevalencia": _prevalencia(base["B2"], y)},
        "pulsos": {"prevalencia": _prevalencia(base["PULSOS"], y)},
        "periodo": {
            "sem_data": int(ano.isna().sum()),
            "pct_2003_2010": float(ano.between(2003, 2010).sum() / ano.notna().sum() * 100),
            "ano_min": int(ano.min()),
            "ano_max": int(ano.max()),
        },
        "auc_univariada": {c: auc_univariada(base[c] if c in config.VAZAMENTO else X[c], y, grupos)
                           for c in config.ATRIBUTOS + config.VAZAMENTO},
        "retornos": _retornos(base, y, grupos),
        "convenio": {
            "categorias_antes": int(base["Convenio_original"].nunique()),
            "categorias_depois": int(base[config.CONVENIO].nunique()),
            "sus": _prevalencia(base[config.CONVENIO], y).get("SUS"),
        },
        "motivo2_sopro": {
            "n": int(motivo2_sopro.sum()),
            "pct_anormal": float(y[motivo2_sopro.to_numpy()].mean() * 100),
            "sem_sopro_confirmado": int(sem_confirmacao.sum()),
            "pct_normal_sem_confirmacao": float((1 - y[sem_confirmacao.to_numpy()].mean()) * 100),
        },
        "prevalencia_por_ano": {int(a): {"n": int(r["size"]), "pct_anormal": float(r["mean"] * 100)}
                                for a, r in por_ano.iterrows()},
        "ordem_id": {"concordancia_vizinhos": float((y_ordenado[1:] == y_ordenado[:-1]).mean()),
                     "esperado_ao_acaso": float(p ** 2 + (1 - p) ** 2)},
    }
    if destino is not None:
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "eda.json").write_text(json.dumps(eda, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    return eda
