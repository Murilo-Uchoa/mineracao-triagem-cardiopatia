from functools import lru_cache
from pathlib import Path

import pandas as pd

import config
import limpeza
import referencia_clinica

PDF_A1 = Path("..") / "avaliação 1" / referencia_clinica.PDF_PA


@lru_cache(maxsize=1)
def _sem_imputacao():
    df, _ = limpeza.limpar(str(config.RAW), imputar=False)
    return df


def test_sem_imputacao_preserva_ausencia():
    df = _sem_imputacao()
    # Contagens de `ausentes_antes_imputacao` no relatório de limpeza da A1.
    assert df["Altura"].isna().sum() == 3453
    assert df["Peso"].isna().sum() == 1957
    assert "FAIXA_ETARIA" not in df.columns


def test_contagens_da_A1():
    df = _sem_imputacao()
    assert len(df) == 11454
    assert (df[config.ALVO] == "Anormal").sum() == 4884


def test_tabela_pa_csv_igual_pdf(tmp_path):
    destino = tmp_path / "tabela_pa.csv"
    referencia_clinica.exportar_tabela_pa(destino, pdf=PDF_A1)
    do_pdf = referencia_clinica.carregar_tabela_pa(PDF_A1)
    do_csv = referencia_clinica.carregar_tabela_pa(destino)
    pd.testing.assert_frame_equal(do_csv, do_pdf)
