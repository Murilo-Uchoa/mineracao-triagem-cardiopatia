"""Guia de estudo da A2 para o grupo: o porquê de cada etapa e a arguição.

    python src/guia.py

Gera guia/Guia_A2.docx (converter em PDF com src/converter_pdf.ps1). Os
números vêm de resultados/; o guia não entra no repositório público.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

RAIZ = Path(__file__).resolve().parents[1]
RES = RAIZ / "resultados"


def ler(nome):
    return json.loads((RES / nome).read_text(encoding="utf-8"))


EDA = ler("eda.json")
COMP = ler("comparacao_5x2cv.json")
INT = ler("interpretacao.json")
NI = {n: ler(f"aninhada_{n}.json") for n in ("dummy", "logistica", "random_forest", "gradient_boosting")}
GRUPO = json.loads((RAIZ / "grupo.json").read_text(encoding="utf-8"))


def num(v, casas=3):
    return ("−" if v < 0 else "") + f"{abs(v):.{casas}f}".replace(".", ",")


def pct(v, casas=1):
    return num(v, casas) + "%"


def mil(n):
    return f"{int(n):,}".replace(",", ".")


def m(modelo, metrica, bloco="limiar_05"):
    return NI[modelo]["resumo"][bloco][metrica]["media"]


def par(a, b):
    return next(p for p in COMP["pares"] if p["a"] == a and p["b"] == b)


def fn(perfil, dim, cat):
    return INT[perfil][dim][cat]["taxa_fn"] * 100


doc = Document()
estilo = doc.styles["Normal"]
estilo.font.name = "Calibri"
estilo.font.size = Pt(11)


def titulo(texto, nivel=1):
    doc.add_heading(texto, level=nivel)


def par_texto(texto, negrito=None):
    p = doc.add_paragraph()
    if negrito:
        p.add_run(negrito).bold = True
    p.add_run(texto)
    return p


def lista(itens):
    for item in itens:
        doc.add_paragraph(item, style="List Bullet")


def pergunta(n, q, r):
    p = doc.add_paragraph()
    run = p.add_run(f"{n}. {q}")
    run.bold = True
    run.font.color.rgb = RGBColor(0x1B, 0x2A, 0x4A)
    doc.add_paragraph(r)


# ------------------------------------------------------------------- capa
t = doc.add_heading("Guia da A2 — triagem de cardiopatia sem vazamento de dados", 0)
t.alignment = WD_ALIGN_PARAGRAPH.LEFT
par_texto("Material interno do grupo para estudar o trabalho e a arguição. Não é entregue. "
          f"Integrantes: {', '.join(GRUPO['integrantes'][:-1])} e {GRUPO['integrantes'][-1]}.")

# ------------------------------------------------------- 1. em uma página
titulo("1. O trabalho em uma página")
par_texto("Prever, só com o que se sabe antes da ausculta do cardiologista, se um atendimento "
          "pediátrico terminará em diagnóstico Normal ou Anormal (classificação binária). O uso "
          "pretendido é a triagem: ordenar a fila do especialista por risco.", "Pergunta. ")
lista([
    f"Base: {mil(EDA['n'])} atendimentos (de {mil(EDA['n_bruto'])} brutos), {pct(EDA['pct_anormal'])} anormais, "
    f"{EDA['atributos_modelo']} atributos; Real Hospital Português (Recife), {min(EDA['prevalencia_por_ano'])}–{max(EDA['prevalencia_por_ano'])}.",
    f"Vazamento de atributo: SOPRO e B2 excluídos — a regra 'tem sopro ⇒ anormal' acerta "
    f"{pct(EDA['sopro']['oner']['acuracia'] * 100)}.",
    f"Vazamento de instância: {EDA['retornos']['pares_consecutivos']} pares de retornos; chave de paciente DN + sexo "
    f"({mil(EDA['retornos']['n_grupos'])} grupos).",
    "Vazamento de pré-processamento: o CSV da A1 vinha imputado na base inteira; a imputação foi para dentro do treino.",
    f"AUC-ROC: piso {num(m('dummy', 'auc_roc'))}; logística {num(m('logistica', 'auc_roc'))}; "
    f"random forest {num(m('random_forest', 'auc_roc'))}; gradient boosting {num(m('gradient_boosting', 'auc_roc'))}.",
    f"5×2cv + Holm: ensembles > logística (p = {num(par('logistica', 'random_forest')['auc_roc']['p_holm'])} e "
    f"{num(par('logistica', 'gradient_boosting')['auc_roc']['p_holm'])}); RF × GB sem diferença significativa (p = "
    f"{num(par('random_forest', 'gradient_boosting')['auc_roc']['p_holm'])}).",
    f"Triagem (GB): sensibilidade {num(m('gradient_boosting', 'sensibilidade', 'triagem'), 2)}, especificidade "
    f"{num(m('gradient_boosting', 'especificidade', 'triagem'), 2)} — prioriza a fila, não substitui a ausculta.",
])

# ------------------------------------------------------- 2. apresentação
titulo("2. Roteiro da apresentação (15 min)")
nomes = GRUPO["integrantes"]
tabela = doc.add_table(rows=1, cols=3)
tabela.style = "Light Grid Accent 1"
for celula, texto in zip(tabela.rows[0].cells, ["Slides", "Quem", "Assunto (≈ 5 min por pessoa)"]):
    celula.text = texto
for faixa, quem, assunto in [
    ("1–5", nomes[0], "Problema, dados e as três formas de vazamento (sopro, auditoria dos atributos, retornos e imputação)"),
    ("6–9", nomes[1], "Pré-processamento, validação aninhada agrupada, algoritmos, métricas e AUC dos modelos"),
    ("10–14", nomes[2], "Teste estatístico, limiar e matrizes de confusão, erros, importância e conclusão"),
]:
    linha = tabela.add_row().cells
    linha[0].text, linha[1].text, linha[2].text = faixa, quem, assunto
par_texto("As notas do apresentador no .pptx trazem a fala de cada slide. A divisão é sugestão; "
          "o enunciado exige que todos apresentem e que qualquer um responda a qualquer pergunta.")

# ------------------------------------------------- 3. cada etapa e o porquê
titulo("3. Cada etapa e o porquê")
titulo("3.1 Vazamento de dados (três formas)", 2)
par_texto(f"SOPRO e B2 são achados da ausculta, o exame que produz o diagnóstico. Sem sopro, "
          f"{pct(EDA['sopro']['prevalencia']['Ausente']['pct_anormal'])} são anormais; com sopro sistólico, "
          f"{pct(EDA['sopro']['prevalencia']['Sistólico']['pct_anormal'])}. Fora da amostra, o SOPRO sozinho tem AUC "
          f"{num(EDA['auc_univariada']['SOPRO']['auc'])}, contra {num(EDA['auc_univariada']['MOTIVO2']['auc'])} do melhor "
          "atributo mantido. B2 sai pelo mesmo mecanismo, ainda que sozinho seja fraco (só ~5% dos registros fogem do normal).",
          "Atributo. ")
par_texto(f"{EDA['retornos']['pares_consecutivos']} pares de IDs consecutivos com mesma DN e sexo, contra "
          f"{num(EDA['retornos']['esperado_ao_acaso'], 1)} ao acaso: o ID é do atendimento, não da criança. "
          "Usamos StratifiedGroupKFold com a chave DN + sexo para que a mesma criança nunca esteja em treino e teste.",
          "Instância. ")
par_texto("Medianas da A1 calculadas na base inteira = parâmetro aprendido com o teste. Agora o ImputadorEstratificado "
          "aprende as medianas só no treino de cada partição.", "Pré-processamento. ")

titulo("3.2 Pré-processamento", 2)
lista([
    "Limpeza da A1 (sentinelas, faixas clínicas, datas, PPA, duplicatas): regras por linha ou fixas → rodam antes da partição (slide 53 do professor).",
    "Numéricas: mediana do estrato sexo × faixa etária (fallback: mediana global do treino) + indicador de ausência + z-score.",
    "Categóricas: 'Não informado' explícito + one-hot (ignora categoria nova no teste).",
    f"Convênio: padronização léxica ({EDA['convenio']['categorias_antes']} → {EDA['convenio']['categorias_depois']} categorias) e frequência no treino. Target encoding não: usa o alvo.",
    "Sem SMOTE/reamostragem: 42,6% é desbalanceamento moderado; class_weight entrou na busca.",
])

titulo("3.3 Validação, métricas e limiar", 2)
lista([
    "Regra de bolso do professor: 1.000 < N ≤ 100.000 → stratified 10-fold. Hold-out é para big data ('refém da sorte').",
    "Nested CV: externo 10 (estima), interno 5 (escolhe hiperparâmetros por AUC-ROC). Mesmas partições para todos os modelos.",
    "AUC-ROC como critério: independe do limiar. AUC-PR olha a classe positiva; piso = prevalência (0,426).",
    "Limiar de triagem: maior limiar com sensibilidade ≥ 0,90 nas previsões fora da dobra do treino externo; aplicado depois ao teste.",
    "Regra de decisão 'score > limiar', como nos slides.",
])

titulo("3.4 Comparação estatística", 2)
par_texto("Um único dataset → Dietterich (1998): 5×2cv t-test (t̃ com 5 g.l., crítico 2,571). O teste t sobre os "
          "10 folds tem erro Tipo I alto (folds dependentes); o resampled t-test é inadequado. Três pares → Holm. "
          "Friedman/Nemenyi/Wilcoxon são para múltiplos datasets (Demšar), não se aplicam aqui.")

# --------------------------------------------------------- 4. perguntas
titulo("4. Perguntas prováveis")
perguntas = [
    ("Qual atributo indica vazamento e por que foi excluído?",
     f"O SOPRO: é o achado da ausculta que define o diagnóstico; sozinho acerta {pct(EDA['sopro']['oner']['acuracia'] * 100)}. "
     "B2 saiu pelo mesmo mecanismo. Um modelo com eles teria métrica alta e utilidade nula para triagem."),
    ("Por que MOTIVO1 e MOTIVO2 ficaram, se a A1 falou em risco de vazamento?",
     f"São o encaminhamento, que existe antes da consulta. A auditoria mostrou que associam, não determinam: a categoria mais forte "
     f"de MOTIVO1 tem 71% de anormais. 'Sopro' em MOTIVO2 é a suspeita de quem encaminhou: {EDA['motivo2_sopro']['sem_sopro_confirmado']} "
     f"crianças não tiveram o sopro confirmado e {pct(EDA['motivo2_sopro']['pct_normal_sem_confirmacao'])} delas eram normais."),
    ("Por que validação aninhada e não hold-out?",
     "N = 11.454 cai na faixa de stratified 10-fold da tabela do professor. O laço interno impede que a escolha de hiperparâmetros veja o teste."),
    ("Por que agrupar por paciente?",
     "Regra de ouro dos slides: o mesmo indivíduo nos dois lados vaza informação. Há retornos comprovados (168 pares contra 2 ao acaso)."),
    ("A chave DN + sexo é perfeita?",
     "Não. Junta crianças diferentes nascidas no mesmo dia (deixa a validação mais rígida, não mais frouxa) e não liga retornos sem DN. Está nas limitações."),
    ("Por que AUC-ROC como critério e não acurácia?",
     "Acurácia engana com classes desbalanceadas (o piso já acerta 57,4%). A AUC mede a ordenação dos pacientes, independente do limiar."),
    ("O que significa o teste 5×2cv dar p < 0,05 na AUC e não na taxa de erro?",
     "Os ensembles ordenam melhor os pacientes, mas no limiar 0,5 acertam praticamente o mesmo número de casos. A vantagem existe e é pequena (~0,01)."),
    ("Por que Holm?",
     "Três comparações ao mesmo tempo aumentam a chance de falso positivo (erro Tipo I); Holm ajusta os valores-p, com mais poder que Bonferroni."),
    ("Por que o desempenho não passa de ~0,79?",
     "Três famílias de algoritmos chegam ao mesmo patamar, o que sugere (não prova) que o limite está na informação disponível antes da ausculta, e não no algoritmo. Não chamamos isso de erro irredutível: isso exigiria conhecer o erro de Bayes."),
    ("RF e GB são equivalentes?",
     f"Não dá para dizer isso. O 5×2cv não rejeitou H0 (p = {num(par('random_forest', 'gradient_boosting')['auc_roc']['p_holm'])}), e não rejeitar H0 não demonstra igualdade — os slides do professor dizem exatamente isso. Falamos em 'sem diferença significativa'."),
    ("Por que PULSOS ficou, se B2 saiu?",
     f"O critério é não ser produzido pela ausculta, o exame que define o diagnóstico. PULSOS vem da palpação; o sinal é raro (pulsos femorais diminuídos em {EDA['pulsos']['prevalencia']['Femorais diminuídos']['n']} crianças) e a importância no modelo é desprezível ({num(INT['importancia']['gradient_boosting']['PULSOS']['media'])} de AUC)."),
    ("O e^β = 3,42 do sopro no encaminhamento é uma razão de chances clássica?",
     "Não exatamente: a logística é regularizada (L2) e usa one-hot completo, então não há categoria de referência única. Lemos como efeito relativo — o maior efeito positivo do modelo."),
    ("O resultado depende dos casos de cardiopatia já estabelecida?",
     f"Um pouco. São {mil(EDA['n'] - INT['sem_cardiopatia_estabelecida']['n'])} encaminhamentos, positivos fáceis para a triagem. Sem eles, a AUC agregada cai de {num(INT['sem_cardiopatia_estabelecida']['auc_roc_todos'])} para {num(INT['sem_cardiopatia_estabelecida']['auc_roc'])} e a sensibilidade de triagem de 0,90 para {num(INT['sem_cardiopatia_estabelecida']['sensibilidade_triagem'], 2)}. Está nas limitações."),
    ("Por que o convênio tem 367 categorias aqui e 368 na A1?",
     "Na A1 a contagem foi feita depois da imputação, quando a ausência virou a categoria 'Não informado'. Aqui contamos as categorias reais, antes de imputar; depois da padronização de caixa, acento e pontuação, sobram 228."),
    ("Como foi escolhido o limiar de triagem? Ele viu o teste?",
     "Não. Em cada partição externa, previsões fora da dobra do treino escolhem o maior limiar com sensibilidade ≥ 0,90; só depois ele é aplicado ao teste."),
    ("O modelo serve para uso clínico?",
     f"Para priorizar a fila, sim: dispensaria {pct(INT['matriz_triagem']['tn'] / (INT['matriz_triagem']['tn'] + INT['matriz_triagem']['fp']) * 100, 0)} "
     f"dos normais perdendo {pct(INT['matriz_triagem']['fn'] / (INT['matriz_triagem']['fn'] + INT['matriz_triagem']['tp']) * 100, 0)} das cardiopatias. "
     "Para substituir o especialista, não."),
    ("Onde o modelo erra?",
     f"Nos encaminhamentos de rotina: parecer cardiológico ({pct(fn('perfil_fn_05', 'motivo1', '5 - Parecer cardiológico'), 0)} de FN no limiar 0,5) e "
     f"check-up ({pct(fn('perfil_fn_05', 'motivo1', '2 - Check-up'), 0)}), e em crianças maiores. "
     f"{pct(INT['perfil_fn_05']['pct_fn_com_sopro'], 0)} dos FN tinham sopro (a ausculta os pegaria), mas, proporcionalmente, o modelo perde mais as cardiopatias sem sopro: "
     f"{pct(fn('perfil_fn_05', 'sopro', 'sem sopro'), 0)} contra {pct(fn('perfil_fn_05', 'sopro', 'com sopro'), 0)}."),
    ("Qual atributo mais importa?",
     f"MOTIVO2 (queda de {num(INT['importancia']['gradient_boosting']['MOTIVO2']['media'])} na AUC ao permutar), depois FC, MOTIVO1 e HDA 1. "
     f"Na logística, o encaminhamento por sopro tem o maior efeito positivo (e^β = {num(INT['logistica']['coeficientes']['cat__MOTIVO2_6 - Sopro']['razao_de_chance'], 2)})."),
    ("Por que importância por permutação e não a do próprio random forest?",
     "A importância por impureza favorece atributos de alta cardinalidade e é medida no treino; a permutação é medida no teste, por atributo original (agrupa o one-hot)."),
    ("Como garantem a reprodutibilidade?",
     "random_state = 42 em tudo, versões fixadas no requirements, `python executar.py` refaz tudo e 7 verificações automáticas no final; números do artigo gerados pelo código."),
    ("Por que excluir as datas?",
     f"A prevalência cai de {pct(EDA['prevalencia_por_ano'][min(EDA['prevalencia_por_ano'])]['pct_anormal'], 0)} para "
     f"{pct(EDA['prevalencia_por_ano'][max(EDA['prevalencia_por_ano'])]['pct_anormal'], 0)} ao longo dos anos; o modelo aprenderia a época, não o paciente."),
    ("O que fariam a seguir?",
     "Validação temporal, calibração das probabilidades, limiar pelos custos clínicos e fonocardiograma digital (estetoscópio eletrônico) na triagem."),
]
for i, (q, r) in enumerate(perguntas, start=1):
    pergunta(i, q, r)

# ------------------------------------------------------ 5. limites e pendências
titulo("5. Limitações e pendências conhecidas")
lista([
    "Um único hospital, 2003–2010, prevalência em queda: generalização temporal não testada.",
    "Chave de paciente aproximada (DN + sexo).",
    "Imputação reduz a variância das medidas (faixas visíveis no gráfico Peso × Altura da A1).",
    "Pendência da A1 não feita: recuperar idades das 119 datas de nascimento ilegíveis (ficam imputadas).",
    "Importância por permutação subestima atributos correlacionados (Peso, Altura, IMC, IDADE).",
])

titulo("6. Como reproduzir")
lista([
    "pip install -r requirements.txt",
    "Colocar UCMF_raw.csv em dados/ (não vai para o repositório: dados de pacientes).",
    "python executar.py  (≈ 25 min em 16 núcleos) ou python executar.py --etapa artefatos",
    "python -m pytest  (testes); python src/verificar_relatorio.py (checa o artigo)",
])

destino = RAIZ / "guia" / "Guia_A2.docx"
destino.parent.mkdir(exist_ok=True)
doc.save(destino)
sys.stdout.reconfigure(encoding="utf-8")
print(f"Gravado: {destino}")
