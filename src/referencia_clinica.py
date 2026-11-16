"""Referências clínicas pediátricas fornecidas com o estudo de caso.

Lê as tabelas de pressão arterial do material complementar (níveis de PA
por idade, sexo e percentil de estatura) e reconstrói a classificação de
hipertensão que origina a variável PPA.

Fontes, ambas no material complementar da disciplina:

  * "Tables of blood pressure for children" — percentis 50/90/95/99 de PAS
    e PAD para meninos e meninas de 1 a 17 anos.
  * "Explanation about the PPA variable" — o diagnóstico de HAS decorre de
    PAS **ou** PAD elevada; a normalidade fica entre os percentis 5 e 95.

Limitação assumida: a classificação exata exige o percentil de estatura do
paciente, que depende das curvas de crescimento NCHS — disponíveis no
material apenas como gráficos, não como tabela. Adota-se por isso a coluna
do percentil 50 de estatura. Ao longo da tabela a diferença entre as
colunas do 5º e do 95º percentil de estatura é de 8 a 10 mmHg na sistólica,
de modo que a aproximação desloca o limiar em no máximo cerca de 5 mmHg.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from pathlib import Path

PDF_PA = "instrucoes/material-complementar/Tables of blood pressure for children.pdf"

# Na A2 a tabela é lida de um CSV extraído uma vez do PDF (dados públicos do
# NHBPEP, 2004), para o repositório rodar sem o material da disciplina. Sem o
# CSV, cai no PDF guardado na pasta da A1.
RAIZ = Path(__file__).resolve().parents[1]
CSV_PA = RAIZ / "dados" / "referencia" / "tabela_pa.csv"
PDF_PA_A1 = RAIZ.parent / "avaliação 1" / PDF_PA

PERCENTIS_ALTURA = [5, 10, 25, 50, 75, 90, 95]
PERCENTIS_PA = [50, 90, 95, 99]

# Faixas plausíveis derivadas das próprias tabelas, com folga para os
# extremos etários que elas não cobrem (lactentes com menos de 1 ano).
# A tabela vai de 34 mmHg (PAD, 1 ano, P50) a 139 mmHg (PAS, 17 anos, P99).
FAIXA_PA = {"PA SISTOLICA": (55.0, 180.0), "PA DIASTOLICA": (25.0, 120.0)}


def carregar_tabela_pa(caminho=None) -> pd.DataFrame:
    """Lê as tabelas de PA em formato longo, do CSV ou do PDF.

    Devolve uma linha por (sexo, idade, percentil de PA, percentil de
    estatura), com as colunas `PAS` e `PAD`. Sem caminho, usa o CSV da A2
    se existir e, senão, o PDF da A1.
    """
    if caminho is None:
        caminho = CSV_PA if CSV_PA.exists() else PDF_PA_A1
    if str(caminho).lower().endswith(".csv"):
        return pd.read_csv(caminho)
    return _tabela_do_pdf(caminho)


def exportar_tabela_pa(destino, pdf=None) -> None:
    """Grava a tabela de PA extraída do PDF num CSV."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    _tabela_do_pdf(pdf or PDF_PA_A1).to_csv(destino, index=False)


def _tabela_do_pdf(caminho) -> pd.DataFrame:
    """Extrai as tabelas de PA do PDF do material complementar."""
    import pypdf

    leitor = pypdf.PdfReader(caminho)
    registros = []

    for pagina in leitor.pages:
        texto = pagina.extract_text() or ""
        # As duas primeiras páginas são meninos; as duas últimas, meninas.
        sexo = "F" if "Girls" in texto else "M"
        idade = None

        for linha in texto.split("\n"):
            linha = linha.strip()
            # "1 50th 80 81 ..." abre um bloco de idade; "90th 94 95 ..."
            # continua o bloco corrente. O "l" no lugar do "1" é um defeito
            # do PDF na tabela das meninas.
            casa = re.match(r"^(?:([l\d]+)\s+)?(50|90|95|99)th\s+(.*)$", linha)
            if not casa:
                continue

            if casa.group(1):
                idade = 1 if casa.group(1) == "l" else int(casa.group(1))
            if idade is None:
                continue

            numeros = [int(n) for n in re.findall(r"\d+", casa.group(3))]
            if len(numeros) != 14:
                continue

            for i, p_altura in enumerate(PERCENTIS_ALTURA):
                registros.append({
                    "SEXO": sexo,
                    "idade": idade,
                    "percentil_pa": int(casa.group(2)),
                    "percentil_altura": p_altura,
                    "PAS": numeros[i],
                    "PAD": numeros[i + 7],
                })

    return pd.DataFrame(registros)


def limiares(tabela: pd.DataFrame, percentil_altura: int = 50) -> pd.DataFrame:
    """Reduz a tabela aos limiares usados na classificação.

    Uma linha por sexo e idade, com as colunas `PAS_90`, `PAS_95`, `PAS_99`
    e as equivalentes de PAD.
    """
    sub = tabela[tabela["percentil_altura"] == percentil_altura]
    largo = sub.pivot_table(
        index=["SEXO", "idade"], columns="percentil_pa", values=["PAS", "PAD"]
    )
    largo.columns = [f"{medida}_{p}" for medida, p in largo.columns]
    return largo.reset_index()


def _classe(valor, l90, l95, l99):
    """Estágio de hipertensão de uma única medida."""
    if pd.isna(valor) or pd.isna(l90):
        return np.nan
    if valor >= l99:
        return "HAS-2"
    if valor >= l95:
        return "HAS-1"
    if valor >= l90:
        return "Pre-Hipertensao"
    return "Normal"


SEVERIDADE = {"Normal": 0, "Pre-Hipertensao": 1, "HAS-1": 2, "HAS-2": 3}


def classificar_ppa(df: pd.DataFrame, tabela: pd.DataFrame | None = None,
                    percentil_altura: int = 50) -> pd.Series:
    """Recalcula PPA a partir de PAS, PAD, sexo e idade.

    A idade é arredondada para o ano inteiro mais próximo dentro de 1 a 17,
    faixa coberta pelas tabelas. Como o diagnóstico decorre de PAS **ou**
    PAD, prevalece a medida de maior gravidade, e o rótulo registra qual
    delas determinou a classificação — o mesmo formato da coluna original
    (`HAS-1 PAS`, `Pre-Hipertensao PAD`, ...).
    """
    tabela = carregar_tabela_pa() if tabela is None else tabela
    lim = limiares(tabela, percentil_altura)

    base = pd.DataFrame({
        "SEXO": df["SEXO"],
        "idade": df["IDADE"].round().clip(1, 17),
        "PAS": df["PA SISTOLICA"],
        "PAD": df["PA DIASTOLICA"],
    })
    base = base.merge(lim, on=["SEXO", "idade"], how="left")

    c_pas = [_classe(v, a, b, c) for v, a, b, c in zip(
        base["PAS"], base["PAS_90"], base["PAS_95"], base["PAS_99"])]
    c_pad = [_classe(v, a, b, c) for v, a, b, c in zip(
        base["PAD"], base["PAD_90"], base["PAD_95"], base["PAD_99"])]

    saida = []
    for cs, cd in zip(c_pas, c_pad):
        if pd.isna(cs) and pd.isna(cd):
            saida.append(np.nan)
            continue
        cs = cs if not pd.isna(cs) else "Normal"
        cd = cd if not pd.isna(cd) else "Normal"
        if SEVERIDADE[cs] == 0 and SEVERIDADE[cd] == 0:
            saida.append("Normal")
        elif SEVERIDADE[cs] >= SEVERIDADE[cd]:
            saida.append(f"{cs} PAS")
        else:
            saida.append(f"{cd} PAD")

    return pd.Series(saida, index=df.index, name="PPA_recalculado")
