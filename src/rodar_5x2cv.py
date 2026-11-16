"""Roda o 5×2-fold CV t-test entre os três modelos (execução longa)."""

import base_dados
import comparacao
import config

if __name__ == "__main__":
    X, y, grupos, _ = base_dados.carregar_base(config.RAW)
    saida = comparacao.rodar_5x2cv(X, y, grupos)
    for par in saida["pares"]:
        print(par["a"], "x", par["b"], {k: round(v, 4) for k, v in par["auc_roc"].items()})
