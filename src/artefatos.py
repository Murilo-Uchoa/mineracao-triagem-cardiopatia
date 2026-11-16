"""Gera, a partir de `resultados/`, os números e as tabelas do artigo.

Nenhum número do relatório é digitado à mão. O texto LaTeX usa
`\\dado{chave}`, e `relatorio/numeros.tex` define cada chave; uma chave
inexistente interrompe a compilação com erro, em vez de sair em branco.
As tabelas vão prontas para `relatorio/tabelas/`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter

import config
import modelos

ROTULO_METRICA = {
    "auc_roc": "AUC-ROC", "auc_pr": "AUC-PR", "acuracia": "Acurácia",
    "acuracia_balanceada": "Acur. bal.", "sensibilidade": "Sensib.",
    "especificidade": "Especif.", "precisao": "Precisão", "f1": "F1",
}


def numero(valor: float, casas: int = 3) -> str:
    texto = f"{abs(valor):.{casas}f}".replace(".", "{,}")
    negativo = valor < 0 and float(f"{abs(valor):.{casas}f}") != 0
    return ("$-$" if negativo else "") + texto


def inteiro(valor: int) -> str:
    return f"{int(valor):,}".replace(",", "{.}")


def pct(valor: float, casas: int = 1) -> str:
    return numero(valor, casas) + "\\%"


def chave(*partes) -> str:
    def limpa(p):
        p = unicodedata.normalize("NFKD", str(p))
        p = "".join(c for c in p if not unicodedata.combining(c)).lower()
        return re.sub(r"[^a-z0-9]", "", p)
    return "-".join(limpa(p) for p in partes)


def _ler(resultados, nome):
    return json.loads((resultados / nome).read_text(encoding="utf-8"))


def _numeros(resultados) -> dict[str, str]:
    eda = _ler(resultados, "eda.json")
    comp = _ler(resultados, "comparacao_5x2cv.json")
    interp = _ler(resultados, "interpretacao.json")
    aninhada = {n: _ler(resultados, f"aninhada_{n}.json") for n in modelos.NOMES}
    d: dict[str, str] = {}

    # Dados e EDA
    d["n"] = inteiro(eda["n"])
    d["n-bruto"] = inteiro(eda["n_bruto"])
    d["pct-normal"] = pct(100 - eda["pct_anormal"])
    d["n-anormal"] = inteiro(eda["n_anormal"])
    d["n-normal"] = inteiro(eda["n"] - eda["n_anormal"])
    d["pct-anormal"] = pct(eda["pct_anormal"])
    d["atributos-brutos"] = str(eda["atributos_brutos"])
    d["atributos-modelo"] = str(eda["atributos_modelo"])
    for k, v in eda["sopro"]["oner"].items():
        d[chave("oner-sopro", k)] = pct(v * 100)
    for cat, v in eda["sopro"]["prevalencia"].items():
        d[chave("prev-sopro", cat)] = pct(v["pct_anormal"])
        d[chave("n-sopro", cat)] = inteiro(v["n"])
    for cat, v in eda["b2"]["prevalencia"].items():
        d[chave("prev-b2", cat)] = pct(v["pct_anormal"])
        d[chave("n-b2", cat)] = inteiro(v["n"])
    for cat, v in eda["pulsos"]["prevalencia"].items():
        d[chave("prev-pulsos", cat)] = pct(v["pct_anormal"], 0)
        d[chave("n-pulsos", cat)] = inteiro(v["n"])
    d["periodo-pct"] = pct(eda["periodo"]["pct_2003_2010"])
    d["sem-data"] = inteiro(eda["periodo"]["sem_data"])
    for atributo, v in eda["auc_univariada"].items():
        d[chave("auc-uni", atributo)] = numero(v["auc"])
    for atributo, v in eda["ausencia_pct"].items():
        d[chave("ausencia", atributo)] = pct(v)
    r = eda["retornos"]
    d["retornos-pares"] = inteiro(r["pares_consecutivos"])
    d["retornos-acaso"] = numero(r["esperado_ao_acaso"], 1)
    d["grupos"] = inteiro(r["n_grupos"])
    d["grupos-multiplos"] = inteiro(r["grupos_multiplos"])
    d["linhas-grupos-multiplos"] = inteiro(r["linhas_em_grupos_multiplos"])
    d["maior-grupo"] = inteiro(r["maior_grupo"])
    d["mesmo-dia"] = inteiro(r["grupos_mesmo_dia"])
    d["mesmo-dia-divergente"] = inteiro(r["mesmo_dia_alvo_divergente"])
    d["sem-dn"] = inteiro(r["linhas_sem_dn"])
    c = eda["convenio"]
    d["convenio-antes"] = inteiro(c["categorias_antes"])
    d["convenio-depois"] = inteiro(c["categorias_depois"])
    if c["sus"]:
        d["sus-n"] = inteiro(c["sus"]["n"])
        d["sus-pct"] = pct(c["sus"]["pct_anormal"])
    m2 = eda["motivo2_sopro"]
    d["m2sopro-n"] = inteiro(m2["n"])
    d["m2sopro-pct"] = pct(m2["pct_anormal"])
    d["m2sopro-semconf"] = inteiro(m2["sem_sopro_confirmado"])
    d["m2sopro-semconf-normal"] = pct(m2["pct_normal_sem_confirmacao"])
    anos = sorted(eda["prevalencia_por_ano"], key=int)
    d["ano-ini"], d["ano-fim"] = anos[0], anos[-1]
    d["prev-ano-ini"] = pct(eda["prevalencia_por_ano"][anos[0]]["pct_anormal"], 0)
    d["prev-ano-fim"] = pct(eda["prevalencia_por_ano"][anos[-1]]["pct_anormal"], 0)
    d["ordem-id-concord"] = numero(eda["ordem_id"]["concordancia_vizinhos"])
    d["ordem-id-acaso"] = numero(eda["ordem_id"]["esperado_ao_acaso"])

    # Validação aninhada
    for nome, res in aninhada.items():
        for bloco, prefixo in (("limiar_05", ""), ("triagem", "tri-")):
            for metrica, v in res["resumo"][bloco].items():
                d[chave(prefixo + nome, metrica)] = numero(v["media"])
                d[chave(prefixo + nome, metrica, "dp")] = numero(v["dp"])
        d[chave(nome, "minutos")] = numero(res["segundos"] / 60, 1)
        sens_folds = [f["metricas_triagem"]["sensibilidade"] for f in res["folds"]]
        d[chave("tri-" + nome, "sensibilidade", "min")] = numero(min(sens_folds), 2)
        d[chave("tri-" + nome, "sensibilidade", "max")] = numero(max(sens_folds), 2)
        if nome != "dummy":
            for p, (valor, vezes) in moda_por_parametro(res["folds"]).items():
                d[chave("hp", nome, p)] = _valor_grade(valor)
                d[chave("hp", nome, p, "n")] = f"{vezes}/10"
        limiares = [f["limiar_triagem"] for f in res["folds"]]
        d[chave(nome, "limiar-min")] = numero(min(limiares), 2)
        d[chave(nome, "limiar-max")] = numero(max(limiares), 2)

    # Comparação estatística
    for par in comp["pares"]:
        for metrica in ("auc_roc", "erro"):
            v = par[metrica]
            base = chave(par["a"], par["b"], metrica)
            d[base + "-dif"] = numero(v["dif_media"])
            d[base + "-absdif"] = numero(abs(v["dif_media"]))
            d[base + "-t"] = numero(v["t"], 2)
            d[base + "-p"] = numero(v["p"])
            d[base + "-pholm"] = numero(v["p_holm"])

    # Interpretação
    melhor = interp["melhor"]
    d["melhor"] = modelos.ROTULOS[melhor]
    for nome_matriz in ("matriz_05", "matriz_triagem"):
        for k, v in interp[nome_matriz].items():
            d[chave(nome_matriz, k)] = inteiro(v)
    mt = interp["matriz_triagem"]
    d["tri-sens-pct"] = pct(mt["tp"] / (mt["tp"] + mt["fn"]) * 100, 0)
    d["tri-normais-dispensados-pct"] = pct(mt["tn"] / (mt["tn"] + mt["fp"]) * 100, 0)
    d["tri-cardiopatias-perdidas-pct"] = pct(mt["fn"] / (mt["fn"] + mt["tp"]) * 100, 0)
    sub = interp["sem_cardiopatia_estabelecida"]
    d["sub-n"] = inteiro(sub["n"])
    d["sub-excluidos"] = inteiro(eda["n"] - sub["n"])
    d["sub-auc"] = numero(sub["auc_roc"])
    d["sub-auc-todos"] = numero(sub["auc_roc_todos"])
    d["sub-sens"] = numero(sub["sensibilidade_triagem"])
    d["sub-espec"] = numero(sub["especificidade_triagem"])
    for perfil in ("perfil_fn_05", "perfil_fn_triagem"):
        p = interp[perfil]
        for campo in ("pct_fn_com_sopro", "pct_positivos_com_sopro", "pct_fn_sem_sopro"):
            d[chave(perfil, campo)] = pct(p[campo])
        for dimensao in ("sopro", "faixa_etaria", "motivo1", "pa_medida"):
            for valor, t in p[dimensao].items():
                d[chave(perfil, dimensao, valor)] = pct(t["taxa_fn"] * 100)
    for nome, imp in interp["importancia"].items():
        for posicao, (atributo, v) in enumerate(imp.items(), start=1):
            d[chave("imp", nome, atributo)] = numero(v["media"])
            d[chave("imp", nome, "top", posicao)] = atributo
    for nome_coef, v in interp["logistica"]["coeficientes"].items():
        d[chave("or", nome_coef)] = numero(v["razao_de_chance"], 2)
    return d


def _tabela_metricas(resultados) -> str:
    aninhada = {n: _ler(resultados, f"aninhada_{n}.json") for n in modelos.NOMES}
    colunas = [("limiar_05", m) for m in ("auc_roc", "auc_pr", "acuracia_balanceada",
                                          "sensibilidade", "especificidade", "f1")]
    colunas += [("triagem", m) for m in ("sensibilidade", "especificidade", "precisao")]
    destaque = {}
    for bloco, m in colunas:
        valores = {n: aninhada[n]["resumo"][bloco][m]["media"] for n in modelos.NOMES if n != "dummy"}
        destaque[(bloco, m)] = melhores(valores)

    linhas = []
    for nome in modelos.NOMES:
        celulas = [modelos.ROTULOS[nome]]
        for bloco, m in colunas:
            v = aninhada[nome]["resumo"][bloco][m]
            texto = f"{numero(v['media'])}\\,$\\pm$\\,{numero(v['dp'])}"
            if nome in destaque[(bloco, m)]:
                texto = f"\\textbf{{{texto}}}"
            celulas.append(texto)
        linhas.append(" & ".join(celulas) + r" \\")
    cab_metricas = " & ".join(ROTULO_METRICA[m] for _, m in colunas)
    return "\n".join([
        r"\begin{tabular}{@{}l" + "c" * len(colunas) + "@{}}",
        r"\toprule",
        r" & \multicolumn{2}{c}{Independentes do limiar} & \multicolumn{4}{c}{Limiar 0{,}5}"
        r" & \multicolumn{3}{c}{Limiar de triagem} \\",
        r"\cmidrule(lr){2-3}\cmidrule(lr){4-7}\cmidrule(l){8-10}",
        f"Modelo & {cab_metricas} \\\\",
        r"\midrule",
        *linhas,
        r"\bottomrule",
        r"\end{tabular}",
    ])


def _valor_grade(v):
    if v is None:
        return "nenhum"
    if v == "balanced":
        return "balanceado"
    if isinstance(v, float):
        return numero(v, 2).rstrip("0").rstrip(",{}") if v != int(v) else str(int(v))
    return str(v)


NOMES_PARAM = {"C": "$C$", "class_weight": "peso de classe", "max_depth": "prof. máx.",
               "min_samples_leaf": "mín. por folha", "learning_rate": "taxa de aprend.",
               "max_leaf_nodes": "folhas máx.", "l2_regularization": "reg. L2"}


def melhores(valores: dict, casas: int = 3) -> set:
    """Modelos empatados no melhor valor, na precisão em que a tabela os mostra."""
    arredondados = {k: round(v, casas) for k, v in valores.items()}
    topo = max(arredondados.values())
    return {k for k, v in arredondados.items() if v == topo}


def moda_por_parametro(folds) -> dict:
    """Valor mais escolhido de cada hiperparâmetro e em quantas partições."""
    saida = {}
    for p in folds[0]["params"]:
        contagem = Counter(json.dumps(f["params"][p]) for f in folds)
        valor, vezes = contagem.most_common(1)[0]
        saida[p] = (json.loads(valor), vezes)
    return saida


def _escolha_por_parametro(folds) -> str:
    """Moda de cada hiperparâmetro; empate no topo aparece como "a ou b"."""
    partes = []
    for p in folds[0]["params"]:
        contagem = Counter(json.dumps(f["params"][p]) for f in folds).most_common()
        topo = [json.loads(v) for v, n in contagem if n == contagem[0][1]]
        valor = " ou ".join(_valor_grade(v) for v in topo)
        cada = " cada" if len(topo) > 1 else ""
        partes.append(f"{NOMES_PARAM[p]} = {valor} ({contagem[0][1]}/10{cada})")
    return "; ".join(partes)


def _tabela_hiperparametros(resultados) -> str:
    linhas = []
    for nome in ("logistica", "random_forest", "gradient_boosting"):
        folds = _ler(resultados, f"aninhada_{nome}.json")["folds"]
        espaco = "; ".join(
            f"{NOMES_PARAM[p.replace('modelo__', '')]} $\\in$ "
            f"\\{{{', '.join(_valor_grade(x) for x in valores)}\\}}"
            for p, valores in modelos.GRADES[nome].items())
        linhas.append(f"{SIGLAS[nome]} & {espaco} & {_escolha_por_parametro(folds)} \\\\")
    coluna = r">{\raggedright\arraybackslash}p"
    return "\n".join([
        r"\begin{tabular}{@{}l" + coluna + r"{0.42\linewidth}" + coluna + r"{0.38\linewidth}@{}}",
        r"\toprule",
        r"Modelo & Espaço de busca & Valor mais escolhido (partições) \\",
        r"\midrule",
        "\n\\addlinespace\n".join(linhas),
        r"\bottomrule",
        r"\end{tabular}",
    ])


SIGLAS = {"logistica": "LR", "random_forest": "RF", "gradient_boosting": "GB"}


def _tabela_testes(resultados) -> str:
    comp = _ler(resultados, "comparacao_5x2cv.json")
    linhas = []
    for par in comp["pares"]:
        a, b = (SIGLAS[par[k]] for k in ("a", "b"))
        auc, erro = par["auc_roc"], par["erro"]
        linhas.append(
            f"{a} $\\times$ {b} & {numero(auc['dif_media'])} & {numero(auc['t'], 2)} & "
            f"{numero(auc['p_holm'])} & {numero(erro['dif_media'])} & {numero(erro['p_holm'])} \\\\")
    return "\n".join([
        r"\begin{tabular}{@{}lccccc@{}}",
        r"\toprule",
        r" & \multicolumn{3}{c}{AUC-ROC} & \multicolumn{2}{c}{Taxa de erro} \\",
        r"\cmidrule(lr){2-4}\cmidrule(l){5-6}",
        r"A $\times$ B & $\overline{\Delta}$ & $\tilde{t}$ & $p_{\mathrm{Holm}}$"
        r" & $\overline{\Delta}$ & $p_{\mathrm{Holm}}$ \\",
        r"\midrule",
        *linhas,
        r"\bottomrule",
        r"\end{tabular}",
    ])


def gerar(resultados=config.RESULTADOS, relatorio=config.RELATORIO) -> None:
    relatorio.mkdir(parents=True, exist_ok=True)
    (relatorio / "tabelas").mkdir(exist_ok=True)
    cabecalho = [
        "% Gerado por src/artefatos.py a partir de resultados/ — não editar à mão.",
        r"\makeatletter",
        r"\providecommand{\defnum}[2]{\@namedef{num@#1}{#2}}",
        r"\providecommand{\dado}[1]{\@ifundefined{num@#1}"
        r"{\PackageError{numeros}{Numero indefinido: #1}{}}{\@nameuse{num@#1}}}",
        r"\makeatother",
    ]
    corpo = [f"\\defnum{{{k}}}{{{v}}}" for k, v in sorted(_numeros(resultados).items())]
    (relatorio / "numeros.tex").write_text("\n".join(cabecalho + corpo) + "\n", encoding="utf-8")
    for nome, funcao in (("tab_metricas", _tabela_metricas),
                         ("tab_hiperparametros", _tabela_hiperparametros),
                         ("tab_testes", _tabela_testes)):
        (relatorio / "tabelas" / f"{nome}.tex").write_text(funcao(resultados) + "\n",
                                                           encoding="utf-8")
