"""As quatro figuras do artigo, em PDF vetorial (e PNG para os slides).

Largura de uma coluna IEEE (3,5 pol.), fonte de 8 pt no estilo Times (STIX),
paleta segura para daltonismo. Todos os valores vêm de `resultados/`.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from sklearn.metrics import precision_recall_curve, roc_curve  # noqa: E402

import config  # noqa: E402
import modelos  # noqa: E402

LARGURA = 3.5
CORES = {"logistica": "#0072B2", "random_forest": "#009E73",
         "gradient_boosting": "#D55E00", "dummy": "#999999"}
COR_VAZAMENTO = "#CC3311"
COR_NEUTRA = "#4477AA"

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix",
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

NOMES_ATRIBUTO = {"HDA 1": "HDA 1", "PA_medida": "PA_medida", "Convenio": "Convênio"}


def _ler(resultados, nome):
    return json.loads((resultados / nome).read_text(encoding="utf-8"))


def _salvar(fig, destino, nome):
    destino.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino / f"{nome}.pdf")
    fig.savefig(destino / f"{nome}.png", dpi=200)
    plt.close(fig)


def _virgula(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def _milhar(n):
    return f"{int(n):,}".replace(",", ".")


def _ptbr(*eixos, y=False):
    """Vírgula decimal nos rótulos numéricos (eixo x; o y só quando numérico)."""
    formato = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    for ax in eixos:
        ax.xaxis.set_major_formatter(formato)
        if y:
            ax.yaxis.set_major_formatter(formato)


def fig_eda(resultados, destino):
    eda = _ler(resultados, "eda.json")
    fig, (a, b) = plt.subplots(2, 1, figsize=(LARGURA, 3.55),
                               gridspec_kw={"height_ratios": [1, 2.6], "hspace": 0.55})

    prev = {k: v for k, v in eda["sopro"]["prevalencia"].items() if v["n"] >= 30}
    cats = sorted(prev, key=lambda k: prev[k]["pct_anormal"])
    valores = [prev[c]["pct_anormal"] for c in cats]
    a.barh(cats, valores, color=COR_VAZAMENTO, height=0.6)
    a.axvline(eda["pct_anormal"], color="black", ls="--", lw=0.8)
    for i, c in enumerate(cats):
        x = max(valores[i], eda["pct_anormal"]) + 1.5
        a.text(x, i, f"{_virgula(valores[i])}% (n = {_milhar(prev[c]['n'])})",
               va="center", fontsize=7)
    a.set_xlim(0, 135)
    a.set_xticks([0, 25, 50, 75, 100])
    a.set_xlabel(f"% de diagnósticos anormais (tracejado: prevalência geral, "
                 f"{_virgula(eda['pct_anormal'])}%)")
    a.set_title("(a) Cardiopatia por categoria de SOPRO", loc="left")

    auc = eda["auc_univariada"]
    ordem = sorted(auc, key=lambda k: auc[k]["auc"])
    cores = [COR_VAZAMENTO if k in config.VAZAMENTO else COR_NEUTRA for k in ordem]
    barras = b.barh([NOMES_ATRIBUTO.get(k, k) for k in ordem],
                    [auc[k]["auc"] - 0.5 for k in ordem], left=0.5, color=cores, height=0.65)
    for barra, k in zip(barras, ordem):
        if k in config.VAZAMENTO:
            barra.set_hatch("////")
            barra.set_edgecolor("white")
        b.text(auc[k]["auc"] + 0.005, barra.get_y() + barra.get_height() / 2,
               _virgula(auc[k]["auc"], 3), va="center", fontsize=7)
    b.set_xlim(0.5, 0.97)
    b.set_xlabel("AUC-ROC do atributo isolado")
    b.set_title("(b) Poder discriminante de cada atributo", loc="left")
    b.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=COR_VAZAMENTO, hatch="////", ec="white"),
                      plt.Rectangle((0, 0), 1, 1, color=COR_NEUTRA)],
             labels=["excluído (vazamento)", "mantido no modelo"],
             loc="lower right", frameon=False)
    _ptbr(a, b)
    _salvar(fig, destino, "fig1_eda")


def _caixa(ax, x, y, w, h, texto, cor="#EEF3F8", borda="#4477AA", peso="normal", tamanho=7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.015",
                                fc=cor, ec=borda, lw=0.8))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tamanho,
            fontweight=peso, linespacing=1.15)


def _seta(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": "#333333"})


def fig_metodologia(destino):
    """Esquema do pipeline e da validação, na largura das duas colunas."""
    fig, ax = plt.subplots(figsize=(7.16, 2.1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    t = 7.2

    # 1. Dados
    _caixa(ax, 0.008, 0.57, 0.15, 0.36, "Dado bruto\n12.873 × 21\n↓ limpeza da A1\n(regras fixas,\nsem imputação)",
           cor="#F2F2F2", borda="#666666", tamanho=t)
    _caixa(ax, 0.008, 0.07, 0.15, 0.42, "Base de modelagem\n11.454 atendimentos\n13 atributos\n(SOPRO e B2\nexcluídos)",
           cor="#F2F2F2", borda="#666666", tamanho=t)
    _seta(ax, 0.083, 0.57, 0.083, 0.495)
    _seta(ax, 0.158, 0.28, 0.186, 0.28)

    # 2. Validação aninhada agrupada
    ax.add_patch(FancyBboxPatch((0.19, 0.03), 0.42, 0.955,
                                boxstyle="round,pad=0.004,rounding_size=0.015",
                                fc="none", ec="#4477AA", lw=1.0, ls=(0, (4, 2))))
    ax.text(0.40, 0.905, "Laço externo: StratifiedGroupKFold, k = 10\n"
            "grupo = paciente (DN + sexo)",
            fontsize=t - 0.8, fontweight="bold", color="#4477AA", ha="center", va="center")
    _caixa(ax, 0.205, 0.07, 0.25, 0.75, "", cor="#FFFFFF", borda="#228833")
    ax.text(0.33, 0.74, "Treino externo (9 partes)", fontsize=t, fontweight="bold",
            color="#228833", ha="center", va="center")
    _caixa(ax, 0.215, 0.38, 0.23, 0.27,
           "Laço interno agrupado, k = 5:\nbusca em grade dos\nhiperparâmetros (AUC-ROC)",
           cor="#EAF5EC", borda="#228833", tamanho=t - 0.4)
    _caixa(ax, 0.215, 0.10, 0.23, 0.23,
           "Limiar de triagem:\nsensibilidade ≥ 0,90 nas\nprevisões fora da dobra",
           cor="#EAF5EC", borda="#228833", tamanho=t - 0.4)
    _caixa(ax, 0.47, 0.07, 0.125, 0.6,
           "Teste externo\n(1 parte)\n\nnenhum paciente\nem comum\ncom o treino\n\nmétricas, curvas,\npermutação",
           cor="#FDF0E6", borda="#D55E00", tamanho=t - 0.6)

    # 3. Pipeline
    _caixa(ax, 0.645, 0.03, 0.355, 0.94, "", cor="#FFFFFF", borda="#666666")
    ax.text(0.8225, 0.90, "Pipeline ajustado só no treino", fontsize=t, fontweight="bold",
            ha="center", va="center")
    etapas = ["Numéricas: mediana por sexo × faixa etária\n+ indicador de ausência → z-score",
              "Categóricas: \"Não informado\" → one-hot",
              "Convênio: frequência no treino → z-score",
              "Modelo: Regressão Logística, Random\nForest ou Gradient Boosting (+ Dummy)"]
    alturas = [0.2, 0.13, 0.13, 0.2]
    y = 0.80
    for texto, h in zip(etapas, alturas):
        y -= h
        _caixa(ax, 0.66, y, 0.325, h - 0.025, texto, cor="#F7F7F7", borda="#999999",
               tamanho=t - 0.6)
        y -= 0.02
    # "ajusta" passa por cima da caixa do teste, do treino até o pipeline.
    _seta(ax, 0.455, 0.735, 0.645, 0.735)
    ax.text(0.55, 0.755, "ajusta", fontsize=t - 0.6, ha="center", style="italic")
    _seta(ax, 0.645, 0.20, 0.595, 0.20)
    _salvar(fig, destino, "fig2_metodologia")


def fig_curvas(resultados, destino):
    previsoes = pd.read_csv(resultados / "previsoes_oof.csv")
    interp = _ler(resultados, "interpretacao.json")
    y = previsoes["y"].to_numpy()
    fig, (roc, pr) = plt.subplots(1, 2, figsize=(LARGURA, 1.85), gridspec_kw={"wspace": 0.38})

    for nome in ("logistica", "random_forest", "gradient_boosting"):
        res = _ler(resultados, f"aninhada_{nome}.json")["resumo"]["limiar_05"]
        proba = previsoes[f"proba_{nome}"].to_numpy()
        fpr, tpr, _ = roc_curve(y, proba)
        prec, rec, _ = precision_recall_curve(y, proba)
        rotulo = modelos.ROTULOS[nome].replace("Regressão ", "")
        roc.plot(fpr, tpr, color=CORES[nome], lw=1,
                 label=f"{rotulo} ({_virgula(res['auc_roc']['media'], 3)})")
        pr.plot(rec, prec, color=CORES[nome], lw=1,
                label=f"{rotulo} ({_virgula(res['auc_pr']['media'], 3)})")

    m = interp["matriz_triagem"]
    sens = m["tp"] / (m["tp"] + m["fn"])
    fpr_t = m["fp"] / (m["fp"] + m["tn"])
    precisao = m["tp"] / (m["tp"] + m["fp"])
    cor = CORES[interp["melhor"]]
    roc.plot(fpr_t, sens, "o", ms=4, mfc="white", mec=cor, mew=1.2)
    pr.plot(sens, precisao, "o", ms=4, mfc="white", mec=cor, mew=1.2)
    roc.annotate("triagem", (fpr_t, sens), xytext=(fpr_t + 0.12, sens - 0.17), fontsize=7,
                 arrowprops={"arrowstyle": "-", "lw": 0.5})

    roc.plot([0, 1], [0, 1], color=CORES["dummy"], lw=0.7, ls=":")
    pr.axhline(y.mean(), color=CORES["dummy"], lw=0.7, ls=":")
    roc.set(xlabel="Taxa de falsos positivos", ylabel="Sensibilidade", xlim=(0, 1), ylim=(0, 1.01))
    pr.set(xlabel="Sensibilidade (recall)", ylabel="Precisão", xlim=(0, 1), ylim=(0.3, 1.01))
    roc.set_title("(a) ROC (AUC-ROC média)", loc="left")
    pr.set_title("(b) PR (AUC-PR média)", loc="left")
    roc.legend(loc="lower right", bbox_to_anchor=(1.06, 0.0), frameon=False,
               handlelength=1.0, fontsize=7)
    pr.legend(loc="lower left", frameon=False, handlelength=1.0, fontsize=7)
    _ptbr(roc, pr, y=True)
    _salvar(fig, destino, "fig3_curvas")


def fig_erros(resultados, destino):
    interp = _ler(resultados, "interpretacao.json")
    melhor = interp["melhor"]
    fig = plt.figure(figsize=(LARGURA, 3.7))
    grade = fig.add_gridspec(2, 2, height_ratios=[1, 1.75], hspace=0.62, wspace=0.55)

    for i, (chave, titulo) in enumerate((("matriz_05", "limiar 0,5"),
                                         ("matriz_triagem", "limiar de triagem"))):
        ax = fig.add_subplot(grade[0, i])
        m = interp[chave]
        matriz = np.array([[m["tn"], m["fp"]], [m["fn"], m["tp"]]])
        ax.imshow(matriz / matriz.sum(axis=1, keepdims=True), cmap="Blues", vmin=0, vmax=1)
        for (r, c), v in np.ndenumerate(matriz):
            taxa = v / matriz[r].sum()
            ax.text(c, r, f"{v:,}".replace(",", ".") + f"\n({_virgula(taxa * 100, 1)}%)",
                    ha="center", va="center", fontsize=7,
                    color="white" if taxa > 0.6 else "black")
        ax.set_xticks([0, 1], ["Normal", "Anormal"])
        ax.set_yticks([0, 1], ["Normal", "Anormal"])
        ax.set_xlabel("Previsto")
        if i == 0:
            ax.set_ylabel("Real")
        ax.set_title(f"({'ab'[i]}) {titulo}", loc="left")
        for lado in ax.spines.values():
            lado.set_visible(False)

    ax = fig.add_subplot(grade[1, :])
    imp = interp["importancia"]
    ordem = list(imp[melhor])[::-1]
    pos = np.arange(len(ordem))
    nomes = list(dict.fromkeys([melhor, "logistica"]))
    altura = 0.38 if len(nomes) == 2 else 0.6
    for j, nome in enumerate(nomes):
        medias = [imp[nome][k]["media"] for k in ordem]
        dps = [imp[nome][k]["dp"] for k in ordem]
        desloc = (j - (len(nomes) - 1) / 2) * altura
        ax.barh(pos + desloc, medias, xerr=dps, height=altura, color=CORES[nome],
                error_kw={"lw": 0.6, "capsize": 1.2},
                label=modelos.ROTULOS[nome])
    ax.set_yticks(pos, [NOMES_ATRIBUTO.get(k, k) for k in ordem])
    ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel("Queda média da AUC-ROC ao permutar o atributo")
    ax.set_title("(c) Importância por permutação (média ± dp nas 10 partições)", loc="left")
    ax.legend(frameon=False, loc="lower right")
    _ptbr(ax)
    _salvar(fig, destino, "fig4_erros")


def gerar_todas(resultados=config.RESULTADOS, destino=config.FIGURAS):
    fig_eda(resultados, destino)
    fig_metodologia(destino)
    fig_curvas(resultados, destino)
    fig_erros(resultados, destino)
