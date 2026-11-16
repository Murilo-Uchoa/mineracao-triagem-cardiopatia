"""Pipeline de limpeza do conjunto UCMF (cardiologia pediátrica).

Cópia do módulo da A1. A única mudança é o parâmetro `imputar` de `limpar`:
a A2 desliga a imputação aqui e a refaz dentro de cada partição de treino.

Organizado segundo a taxonomia de problemas de qualidade da disciplina
(Mineração de Dados / KDD — Prof. Rogerio Salvini):

    ausentes | duplicados | inconsistentes | atípicos (ruído x outlier)

As inconsistências são ainda separadas em léxica, de domínio, lógica,
temporal e de formato, seguindo os slides de limpeza de dados.

Cada função é pura: recebe e devolve um DataFrame, sem efeito colateral.
O orquestrador `limpar` devolve também um relatório com as contagens de
cada intervenção, usado para montar as tabelas do relatório A1.
"""

from __future__ import annotations

import unicodedata

import numpy as np
import pandas as pd

ALVO = "NORMAL X ANORMAL"
ID = "ID"

NUMERICAS = [
    "Peso", "Altura", "IMC", "IDADE",
    "PA SISTOLICA", "PA DIASTOLICA", "FC",
]
DATAS = ["Atendimento", "DN"]
CATEGORICAS = [
    "Convenio", "PULSOS", "PPA", ALVO, "B2", "SOPRO",
    "HDA 1", "HDA2", "SEXO", "MOTIVO1", "MOTIVO2",
]

# Faixas plausíveis em cardiologia pediátrica (pacientes de 0 a 19 anos).
# Valores fora destes limites são tratados como ruído e convertidos em
# ausentes — "excluir o valor atípico e tratar como valor ausente".
FAIXAS_CLINICAS = {
    "Peso": (0.5, 150.0),     # kg — prematuro extremo até adolescente obeso
    "Altura": (30.0, 200.0),  # cm
    "IMC": (8.0, 60.0),       # kg/m²
    "IDADE": (0.0, 19.0),     # anos — faixa declarada pelo próprio conjunto
    "FC": (40.0, 220.0),      # bpm — bradicardia até taquicardia neonatal
    # Limites de PA ancorados nas tabelas do material complementar, que vão
    # de 80 a 143 mmHg (PAS) e de 34 a 94 mmHg (PAD) entre o percentil 50 de
    # 1 ano e o percentil 99 de 17 anos, com folga para lactentes.
    "PA SISTOLICA": (55.0, 180.0),   # mmHg
    "PA DIASTOLICA": (25.0, 120.0),  # mmHg
}

# Sentinelas: valores que ocupam a célula mas não carregam informação.
SENTINELAS_ZERO = ["Peso", "Altura", "IMC"]
SENTINELA_PPA = "#VALUE!"         # erro de fórmula do Excel vazado para o dado
SENTINELA_SEXO = "indeterminado"  # marcador de preenchimento, não um 3º sexo

# Rótulo que `reconstruir_ppa` dá ao PPA quando falta insumo para o cálculo.
# É categoria legítima, mas não é informação sobre o paciente.
PPA_NAO_AFERIDA = "Não aferida"

# Medida registrada como intervalo: "80-90" ou "156 a 168".
INTERVALO = r"(\d+(?:\.\d+)?)\s*(?:-|a)\s*(\d+(?:\.\d+)?)"

EXCEL_EPOCH = pd.Timestamp("1899-12-30")


def _sem_acento(texto):
    """Minúsculas, sem acento e sem espaços nas bordas, para comparação."""
    if not isinstance(texto, str):
        return texto
    normalizado = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in normalizado if not unicodedata.combining(c))


# Rótulos canônicos por variável, indexados pela forma sem acento/minúscula.
# Resolve a inconsistência léxica ("Masculino", "masculino", "M").
MAPAS_CANONICOS = {
    "SEXO": {"m": "M", "masculino": "M", "f": "F", "feminino": "F"},
    ALVO: {
        "normal": "Normal", "normais": "Normal",
        "anormal": "Anormal", "anormais": "Anormal",
    },
    "PULSOS": {
        "normais": "Normais", "amplos": "Amplos",
        "diminuidos": "Diminuídos",
        "femorais diminuidos": "Femorais diminuídos",
        "outro": "Outro",
    },
    "SOPRO": {
        "ausente": "Ausente", "sistolico": "Sistólico",
        "diastolico": "Diastólico", "continuo": "Contínuo",
        "sistolico e diastolico": "Sistólico e diastólico",
    },
    "B2": {
        "normal": "Normal", "hiperfonetica": "Hiperfonética",
        "desdob fixo": "Desdob fixo", "unica": "Única", "outro": "Outro",
    },
}


def carregar_bruto(caminho="dados/UCMF_raw.csv"):
    """Lê o CSV inteiro como texto, para não perder nenhuma anomalia."""
    return pd.read_csv(caminho, encoding="utf-8", dtype=str)


def ler_datas(serie):
    """Lê uma coluna de datas e diz qual formato reconheceu cada célula.

    Tenta, nesta ordem, `DD/MM/AA`, `DD/MM/AAAA` e o número de série do
    Excel. Devolve as datas, ainda sem a correção de século, e o formato de
    cada célula: um dos três, "ilegível" ou ausente, se a célula era vazia.
    """
    formato = pd.Series(None, index=serie.index, dtype=object)

    datas = pd.to_datetime(serie, format="%d/%m/%y", errors="coerce")
    formato[datas.notna()] = "DD/MM/AA"

    falta = datas.isna() & serie.notna()
    longas = pd.to_datetime(serie.where(falta), format="%d/%m/%Y", errors="coerce")
    formato[longas.notna()] = "DD/MM/AAAA"
    datas = datas.fillna(longas)

    falta = datas.isna() & serie.notna()
    serial = pd.to_numeric(serie.where(falta), errors="coerce")
    serial = serial.where(serial.between(1, 80000))
    formato[serial.notna()] = "série do Excel"
    datas = datas.fillna(EXCEL_EPOCH + pd.to_timedelta(serial, unit="D"))

    formato[datas.isna() & serie.notna()] = "ilegível"
    return datas, formato


def converter_datas(df):
    """Unifica os três formatos presentes e corrige a ambiguidade de século.

    Inconsistência de formato: a mesma coluna traz `DD/MM/AA`, `DD/MM/AAAA`
    e o número de série do Excel (ex.: `38574`), resíduo da exportação. O
    que nenhum dos três reconhece ("4/anos", "18/10,1996") vira ausência.

    Inconsistência temporal: o ano de dois dígitos faz `66` virar 2066. Toda
    data posterior a hoje recua um século.
    """
    df = df.copy()
    for col in DATAS:
        datas, _ = ler_datas(df[col])
        futuro = datas > pd.Timestamp.today()
        df[col] = datas.mask(futuro, datas - pd.DateOffset(years=100))
    return df


def _texto_numerico(serie):
    """Texto sem bordas e com ponto decimal, pronto para a conversão."""
    return serie.astype("string").str.strip().str.replace(",", ".", regex=False)


def eh_intervalo(serie):
    """Marca os registros escritos como intervalo em vez de uma medida."""
    return _texto_numerico(serie).str.fullmatch(INTERVALO).fillna(False).astype(bool)


def converter_numericas(df):
    """Converte texto em número, resolvendo vírgula decimal e intervalos.

    Alguns registros de FC trazem um intervalo (`80-90`, `156 a 168`) em vez
    de uma medida. Adota-se o ponto médio, que é a correção possível sem
    descartar a linha; valores absurdos resultantes caem depois na faixa
    clínica.
    """
    df = df.copy()
    for col in NUMERICAS:
        texto = _texto_numerico(df[col])
        valor = pd.to_numeric(texto, errors="coerce").astype("float64")

        extremos = texto.str.extract(f"^{INTERVALO}$").apply(pd.to_numeric, errors="coerce")
        intervalo = extremos.notna().all(axis=1)
        if intervalo.any():
            valor.loc[intervalo] = extremos[intervalo].mean(axis=1)
        df[col] = valor
    return df


def tratar_sentinelas(df):
    """Converte marcadores de não-preenchimento em ausência declarada.

    São três casos distintos, todos invisíveis para `isna()` no dado bruto:
    zero em medidas antropométricas, `#VALUE!` em PPA e `Indeterminado`
    em SEXO. Reconhecê-los é o que revela a ausência real dos dados.
    """
    df = df.copy()
    for col in SENTINELAS_ZERO:
        df[col] = df[col].where(df[col] > 0)
    df["PPA"] = df["PPA"].replace(SENTINELA_PPA, np.nan)
    df["SEXO"] = df["SEXO"].mask(
        df["SEXO"].map(_sem_acento) == SENTINELA_SEXO, np.nan
    )
    return df


def padronizar_texto(df):
    """Resolve a inconsistência léxica das categóricas.

    Unifica caixa e acentuação e projeta cada valor no rótulo canônico da
    variável. Colunas sem mapa explícito recebem apenas limpeza de bordas.
    """
    df = df.copy()
    for col in CATEGORICAS:
        serie = df[col].astype("string").str.strip()
        mapa = MAPAS_CANONICOS.get(col)
        if mapa:
            chave = serie.map(_sem_acento)
            serie = chave.map(mapa).fillna(serie)
        df[col] = serie.replace({"": np.nan})
    return df


def tratar_inconsistencias_dominio(df):
    """Anula valores fora da faixa clínica: ruído, não paciente real."""
    df = df.copy()
    for col, (minimo, maximo) in FAIXAS_CLINICAS.items():
        df[col] = df[col].where(df[col].between(minimo, maximo))
    return df


def tratar_inconsistencia_logica(df):
    """Anula o par de pressão em que a diastólica não fica abaixo da sistólica."""
    df = df.copy()
    invalido = df["PA DIASTOLICA"] >= df["PA SISTOLICA"]
    df.loc[invalido, ["PA SISTOLICA", "PA DIASTOLICA"]] = np.nan
    return df


def tratar_inconsistencia_temporal(df):
    """Anula pares de datas em que o atendimento antecede o nascimento."""
    df = df.copy()
    impossivel = df["Atendimento"] < df["DN"]
    df.loc[impossivel, DATAS] = pd.NaT
    return df


def recalcular_derivadas(df):
    """Reconstrói IDADE e IMC a partir das variáveis de origem.

    É a solução "recalcular a partir de outros dados": corrige a
    inconsistência lógica e, de quebra, preenche ausências sem recorrer a
    imputação estatística. Sobrescreve o valor original apenas quando há
    insumo válido para o cálculo.
    """
    df = df.copy()

    idade = (df["Atendimento"] - df["DN"]).dt.days / 365.25
    idade = idade.where(idade.between(*FAIXAS_CLINICAS["IDADE"]))
    df["IDADE"] = idade.fillna(df["IDADE"])

    altura_m = df["Altura"] / 100
    imc = df["Peso"] / altura_m.pow(2)
    imc = imc.replace([np.inf, -np.inf], np.nan)
    imc = imc.where(imc.between(*FAIXAS_CLINICAS["IMC"]))
    df["IMC"] = imc.fillna(df["IMC"])
    return df


def reconstruir_ppa(df):
    """Recompõe PPA a partir de PAS, PAD, sexo e idade.

    PPA é derivada: classifica a pressão arterial contra as tabelas de
    percentil pediátrico. Os 70% de "Não Calculado" não são uma ausência
    qualquer — são o resultado de faltar algum insumo do cálculo. Onde os
    insumos existem, a classificação é refeita a partir das tabelas do
    material complementar, preservando o valor original onde ele já traz
    uma classificação real.

    Devolve o DataFrame e as contagens de preenchimento e concordância.
    """
    import referencia_clinica

    df = df.copy()
    recalculado = referencia_clinica.classificar_ppa(df)

    sem_classe = df["PPA"].isna() | (df["PPA"] == "Não Calculado")
    comparavel = ~sem_classe & recalculado.notna()
    original = df.loc[comparavel, "PPA"].str.replace(
        "Pre-Hipertensão", "Pre-Hipertensao", regex=False
    )
    concordam = int((original == recalculado[comparavel]).sum())

    # Quão longe ficam as divergências: 0 é o mesmo estágio com outra medida
    # determinante (PAS no lugar de PAD), 1 é a classe vizinha.
    def estagio(rotulos):
        return (rotulos.str.replace(r"\s+(PAS|PAD)$", "", regex=True)
                .map(referencia_clinica.SEVERIDADE))

    divergem = original != recalculado[comparavel]
    distancia = (estagio(original) - estagio(recalculado[comparavel])).abs()[divergem]

    ganhou_classe = sem_classe & recalculado.notna()
    preenchidos = int(ganhou_classe.sum())
    hipertensos = int((ganhou_classe & (recalculado != "Normal")).sum())
    ppa = df["PPA"].where(~sem_classe).fillna(recalculado)

    # Colapsa o sufixo PAS/PAD: ele apenas registra qual das duas medidas
    # determinou o estágio, e o diagnóstico decorre de "PAS ou PAD". Sobra
    # uma ordinal de gravidade em cinco níveis. "Não aferida" é categoria
    # legítima — a consulta não mediu a pressão, fato já sinalizado por
    # `PA_medida` — e não uma ausência a imputar.
    gravidade = (
        ppa.str.replace(r"\s+(PAS|PAD)$", "", regex=True)
        .str.replace("Pre-Hipertensão", "Pré-hipertensão", regex=False)
        .str.replace("Pre-Hipertensao", "Pré-hipertensão", regex=False)
    )
    df["PPA"] = gravidade.fillna(PPA_NAO_AFERIDA)

    return df, {
        "ppa_reconstruidos": preenchidos,
        "ppa_reconstruidos_hipertensos": hipertensos,
        "ppa_comparaveis": int(comparavel.sum()),
        "ppa_concordancia_%": round(concordam / max(int(comparavel.sum()), 1) * 100, 1),
        "ppa_divergentes": int(divergem.sum()),
        "ppa_divergentes_vizinhas": int((distancia <= 1).sum()),
    }


def linhas_vazias(df):
    """Marca os registros sem nenhum atributo informado além do ID e do alvo.

    O `Não aferida` do PPA não conta: ele é atribuído pelo próprio pipeline,
    em `reconstruir_ppa`, justamente quando falta insumo. Contá-lo como
    informação faria toda linha parecer preenchida.
    """
    atributos = [c for c in df.columns if c not in (ID, ALVO)]
    preenchido = df[atributos].notna()
    if "PPA" in preenchido.columns:
        preenchido["PPA"] &= df["PPA"] != PPA_NAO_AFERIDA
    return ~preenchido.any(axis=1)


def remover_sem_informacao(df):
    """Descarta objetos que não sustentam análise supervisionada.

    Duas situações: alvo ausente (não se imputa a variável dependente) e
    registros em que todos os 19 atributos estão vazios após o tratamento
    de sentinelas — linhas que existem apenas como número de ID.
    """
    return df[df[ALVO].notna() & ~linhas_vazias(df)].copy()


def tratar_duplicatas(df):
    """Remove contradições e objetos idênticos, nesta ordem.

    O ID é ignorado na comparação: ele é único por construção e mascararia
    a duplicação. Grupos idênticos nos atributos mas com alvo divergente
    são contradições e saem por inteiro, pois não há critério para escolher
    entre os diagnósticos conflitantes. Dos objetos restantes que se
    repetem, preserva-se uma ocorrência.

    Devolve o DataFrame e as duas contagens separadas.
    """
    atributos = [c for c in df.columns if c not in (ID, ALVO)]

    grupos = df.groupby(atributos, dropna=False)[ALVO]
    alvos = grupos.transform("nunique")
    tamanho = grupos.transform("size")
    sem_contradicao = df[alvos <= 1].copy()
    n_contradicao = len(df) - len(sem_contradicao)

    final = sem_contradicao.drop_duplicates(subset=atributos, keep="first").copy()
    n_duplicata = len(sem_contradicao) - len(final)

    return final, {
        "contradicoes": n_contradicao,
        # O maior grupo contraditório revela se a "contradição" é de paciente
        # real ou de ficha preenchida por modelo, com os mesmos valores padrão.
        "maior_grupo_contraditorio": int(tamanho[alvos > 1].max()) if n_contradicao else 0,
        "duplicatas_exatas": n_duplicata,
    }


def reduzir_atributos(df, limite=0.5):
    """Descarta atributos com ausência acima do limite (regra dos 50%).

    Antes de descartar a pressão arterial, registra-se em `PA_medida` o
    fato de a aferição ter ocorrido: a ausência aqui não é aleatória — ela
    distingue a consulta que mediu a pressão da que não mediu — e
    "a ausência do valor pode ser uma informação".
    """
    df = df.copy()
    df["PA_medida"] = df["PA SISTOLICA"].notna() & df["PA DIASTOLICA"].notna()

    proporcao = df.isna().mean()
    descartados = sorted(proporcao[proporcao > limite].index)
    return df.drop(columns=descartados), descartados


def faixa_etaria(idade):
    """Discretiza a idade nas faixas usuais da pediatria."""
    return pd.cut(
        idade,
        bins=[-0.01, 2, 6, 12, 19],
        labels=["Lactente", "Pré-escolar", "Escolar", "Adolescente"],
    )


def _imputar(df):
    """Preenche numéricas pela mediana estratificada por sexo e faixa etária.

    Versão da A1, sobre a base inteira. A A2 não a usa: ver
    `transformadores.ImputadorEstratificado`.

    A mediana resiste melhor à assimetria que a média, e a estratificação
    evita atribuir a um recém-nascido o peso mediano de um adolescente.
    Categóricas recebem a categoria explícita "Não informado", preservando
    a informação de que o dado faltou.
    """
    df = df.copy()

    # As categóricas vêm primeiro para que toda linha tenha um estrato,
    # e a idade antes das demais numéricas porque ela define esse estrato.
    for col in CATEGORICAS:
        if col == ALVO or col not in df.columns:
            continue
        df[col] = df[col].astype("object").fillna("Não informado")

    df["IDADE"] = df["IDADE"].fillna(df["IDADE"].median())
    df["FAIXA_ETARIA"] = faixa_etaria(df["IDADE"])

    for col in NUMERICAS:
        if col == "IDADE" or col not in df.columns:
            continue
        mediana = df.groupby(["SEXO", "FAIXA_ETARIA"], observed=True)[col]
        df[col] = df[col].fillna(mediana.transform("median"))
        df[col] = df[col].fillna(df[col].median())
    return df


def _celulas(df):
    """Número de células preenchidas, para medir o efeito de cada etapa."""
    return int(df.notna().sum().sum())


def limpar(caminho="dados/UCMF_raw.csv", imputar=True):
    """Executa o pipeline completo e devolve o dado limpo mais o relatório.

    Na A2, `imputar=False`: a imputação tem parâmetros (medianas) e por isso
    passa para dentro do pipeline de modelagem, ajustada só no treino de cada
    partição. Todo o resto é regra por linha ou critério fixo, e roda antes da
    partição, como no pipeline dos slides de experimentação.
    """
    bruto = carregar_bruto(caminho)
    rel = {"linhas_brutas": len(bruto), "colunas": bruto.shape[1]}

    rel["formatos_de_data"], rel["datas_recuadas_um_seculo"] = {}, {}
    for col in DATAS:
        datas, formato = ler_datas(bruto[col])
        rel["formatos_de_data"][col] = {k: int(n) for k, n in formato.value_counts().items()}
        rel["datas_recuadas_um_seculo"][col] = int((datas > pd.Timestamp.today()).sum())
    # Datas preenchidas que nenhum dos três formatos reconhece ("4/anos",
    # "18/10,1996"): viram ausência, e a contagem fica registrada.
    rel["datas_ilegiveis"] = {
        col: rel["formatos_de_data"][col].get("ilegível", 0) for col in DATAS
    }
    df = converter_datas(bruto)
    rel["fc_intervalos"] = int(eh_intervalo(bruto["FC"]).sum())
    df = converter_numericas(df)
    df = padronizar_texto(df)

    antes = _celulas(df)
    df = tratar_sentinelas(df)
    rel["celulas_sentinela"] = antes - _celulas(df)

    # Valores impossíveis, contados por classe de inconsistência.
    faixas = list(FAIXAS_CLINICAS)
    antes = df[faixas].notna().sum()
    df = tratar_inconsistencias_dominio(df)
    por_coluna = antes - df[faixas].notna().sum()
    rel["fora_da_faixa_por_coluna"] = {col: int(n) for col, n in por_coluna.items() if n}
    rel["celulas_fora_da_faixa"] = int(por_coluna.sum())

    antes = _celulas(df)
    df = tratar_inconsistencia_logica(df)
    rel["celulas_pa_invertida"] = antes - _celulas(df)

    rel["atendimentos_antes_do_nascimento"] = int((df["Atendimento"] < df["DN"]).sum())
    antes = _celulas(df)
    df = tratar_inconsistencia_temporal(df)
    rel["celulas_datas_impossiveis"] = antes - _celulas(df)

    rel["celulas_impossiveis"] = (rel["celulas_fora_da_faixa"] + rel["celulas_pa_invertida"]
                                  + rel["celulas_datas_impossiveis"])

    antes_derivadas = df[["IDADE", "IMC"]].copy()
    df = recalcular_derivadas(df)
    rel["derivadas_recuperadas"] = (
        antes_derivadas.isna().sum() - df[["IDADE", "IMC"]].isna().sum()
    ).to_dict()
    rel["derivadas_corrigidas"] = {
        col: int(
            (
                (antes_derivadas[col] - df[col]).abs() > 0.5
            ).sum()
        )
        for col in ["IDADE", "IMC"]
    }

    df, ppa = reconstruir_ppa(df)
    rel.update(ppa)

    vazias = linhas_vazias(df)
    rel["linhas_vazias"] = int(vazias.sum())
    rel["linhas_vazias_sem_alvo"] = int((vazias & df[ALVO].isna()).sum())

    n = len(df)
    sem_alvo = int(df[ALVO].isna().sum())
    df = remover_sem_informacao(df)
    rel["linhas_sem_alvo"] = sem_alvo
    rel["linhas_vazias_com_alvo"] = n - len(df) - sem_alvo
    rel["linhas_sem_informacao"] = n - len(df)

    df, contagens = tratar_duplicatas(df)
    rel.update(contagens)

    df, descartados = reduzir_atributos(df)
    rel["atributos_descartados"] = descartados

    rel["ausentes_antes_imputacao"] = {
        k: int(v) for k, v in df.isna().sum().items() if v
    }
    if imputar:
        df = _imputar(df)

    rel["linhas_finais"] = len(df)
    rel["colunas_finais"] = df.shape[1]
    return df, rel
