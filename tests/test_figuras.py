import pytest

import config
import graficos as figuras

ESPERADAS = ["fig1_eda", "fig2_metodologia", "fig3_curvas", "fig4_erros"]


def test_figuras_existem(tmp_path):
    if not (config.RESULTADOS / "interpretacao.json").exists():
        pytest.skip("resultados ainda não gerados")
    figuras.gerar_todas(config.RESULTADOS, tmp_path)
    for nome in ESPERADAS:
        for ext in ("pdf", "png"):
            arquivo = tmp_path / f"{nome}.{ext}"
            assert arquivo.exists() and arquivo.stat().st_size > 5000


def test_metodologia_nao_depende_de_resultados(tmp_path):
    figuras.fig_metodologia(tmp_path)
    assert (tmp_path / "fig2_metodologia.pdf").exists()
