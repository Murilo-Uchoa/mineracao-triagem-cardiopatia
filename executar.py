"""Reproduz a A2 do estudo de caso UCMF, do CSV bruto às figuras do artigo.

    python executar.py                     # tudo (cerca de 25 min em 16 núcleos)
    python executar.py --etapa artefatos   # só figuras e tabelas, dos resultados salvos
    python executar.py --etapa verificar   # só as verificações

Etapas, na ordem: limpeza → aninhada → 5x2cv → eda → interpretacao →
artefatos → verificar. Precisa de `dados/UCMF_raw.csv` (ver README).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))
sys.stdout.reconfigure(encoding="utf-8")  # acentos no console do Windows

import numpy as np  # noqa: E402

import artefatos  # noqa: E402
import auditoria  # noqa: E402
import base_dados  # noqa: E402
import comparacao  # noqa: E402
import config  # noqa: E402
import experimento  # noqa: E402
import graficos  # noqa: E402
import interpretacao  # noqa: E402
import modelos  # noqa: E402
from transformadores import CodificadorFrequencia, ImputadorEstratificado  # noqa: E402

ETAPAS = ["limpeza", "aninhada", "5x2cv", "eda", "interpretacao", "artefatos", "verificar"]


def verificar(X, y, grupos) -> list[tuple[str, bool]]:
    """As verificações da seção 9.16 do design."""
    checagens = []

    def checa(descricao, ok):
        checagens.append((descricao, bool(ok)))

    checa("SOPRO e B2 fora da matriz de atributos",
          not set(config.VAZAMENTO) & set(X.columns))
    checa("X tem exatamente os 13 atributos do design", list(X.columns) == config.ATRIBUTOS)
    checa("11.454 atendimentos e 42,6% de anormais",
          len(y) == 11454 and round(y.mean() * 100, 1) == 42.6)

    sobreposicao = 0
    for tr, te in experimento.particoes(y, grupos, config.N_EXTERNO, config.SEED):
        sobreposicao += len(set(grupos[tr]) & set(grupos[te]))
        for a, b in experimento._separador_interno(config.N_INTERNO, config.SEED).split(
                X.iloc[tr], y[tr], grupos[tr]):
            sobreposicao += len(set(grupos[tr][a]) & set(grupos[tr][b]))
    for seed in config.SEEDS_5X2:
        for tr, te in experimento.particoes(y, grupos, 2, seed):
            sobreposicao += len(set(grupos[tr]) & set(grupos[te]))
    checa("nenhum paciente em treino e teste (externo, interno e 5×2cv)", sobreposicao == 0)

    prep = modelos.montar_pipeline("logistica").named_steps["prep"]
    ramos = {nome: ramo for nome, ramo, _ in prep.transformers}
    checa("imputação e frequência dentro do pipeline",
          isinstance(ramos["num"].named_steps["imputacao"], ImputadorEstratificado)
          and isinstance(ramos["conv"].named_steps["frequencia"], CodificadorFrequencia))

    esperados = [f"aninhada_{n}.json" for n in modelos.NOMES] + [
        "comparacao_5x2cv.json", "eda.json", "interpretacao.json", "previsoes_oof.csv"]
    checa("todos os resultados presentes",
          all((config.RESULTADOS / e).exists() for e in esperados))
    if (config.RESULTADOS / "aninhada_dummy.json").exists():
        dummy = json.loads((config.RESULTADOS / "aninhada_dummy.json").read_text(encoding="utf-8"))
        checa("piso de referência com AUC 0,5",
              abs(dummy["resumo"]["limiar_05"]["auc_roc"]["media"] - 0.5) < 1e-9)
    return checagens


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--etapa", choices=["tudo"] + ETAPAS, default="tudo")
    etapas = ETAPAS if (e := parser.parse_args().etapa) == "tudo" else [e]

    if not config.RAW.exists():
        sys.exit(f"Falta {config.RAW}. Veja o README para obter o conjunto de dados.")
    X, y, grupos, base = base_dados.carregar_base(config.RAW)
    print(f"Base: {len(y)} atendimentos, {X.shape[1]} atributos, "
          f"{y.mean() * 100:.1f}% anormais, {len(set(grupos))} pacientes (chave DN + sexo)")

    for etapa in etapas:
        inicio = time.time()
        if etapa == "aninhada":
            experimento.rodar_todos(X, y, grupos, base)
        elif etapa == "5x2cv":
            comparacao.rodar_5x2cv(X, y, grupos)
        elif etapa == "eda":
            auditoria.rodar(base, X, y, grupos)
        elif etapa == "interpretacao":
            interpretacao.rodar(X, y, base)
        elif etapa == "artefatos":
            graficos.gerar_todas(config.RESULTADOS, config.FIGURAS)
            artefatos.gerar(config.RESULTADOS, config.RELATORIO)
        elif etapa == "verificar":
            checagens = verificar(X, y, np.asarray(grupos))
            for descricao, ok in checagens:
                print(f"  [{'OK' if ok else 'FALHOU'}] {descricao}")
            if not all(ok for _, ok in checagens):
                sys.exit("Verificações falharam.")
        if etapa != "limpeza":
            print(f"{etapa}: {time.time() - inicio:.0f} s")


if __name__ == "__main__":
    main()
