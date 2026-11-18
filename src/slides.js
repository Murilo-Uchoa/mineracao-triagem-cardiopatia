/**
 * Gera a apresentação de 15 min da A2, no mesmo sistema visual da A1.
 *
 *   node src/slides.js
 *
 * Enunciado: 15 min, ênfase em metodologia e resultados; slides padronizados,
 * numerados, com pouco texto e elementos legíveis. Catorze slides, uma
 * mensagem por slide (cerca de 1 min cada); o detalhe fica nas notas do
 * apresentador. Todos os números vêm de resultados/*.json.
 */

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const GRUPO = require("./grupo");

const RAIZ = path.resolve(__dirname, "..");
const ler = (nome) => JSON.parse(fs.readFileSync(path.join(RAIZ, "resultados", nome), "utf8"));
const EDA = ler("eda.json");
const COMP = ler("comparacao_5x2cv.json");
const INT = ler("interpretacao.json");
const NI = Object.fromEntries(["dummy", "logistica", "random_forest", "gradient_boosting"]
  .map((n) => [n, ler(`aninhada_${n}.json`)]));

// ---------------------------------------------------------------- formatação
const num = (v, casas = 3) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(casas).replace(".", ",");
const pct = (v, casas = 1) => num(v, casas) + "%";
const mil = (n) => Number(n).toLocaleString("pt-BR");
const media = (modelo, metrica, bloco = "limiar_05") => NI[modelo].resumo[bloco][metrica].media;
const par = (a, b) => COMP.pares.find((p) => p.a === a && p.b === b);
const fn = (perfil, dim, cat) => INT[perfil][dim][cat].taxa_fn * 100;
const NOME_ATRIBUTO = { Convenio: "Convênio" };
const nomeAtributo = (k) => NOME_ATRIBUTO[k] || k;

// --------------------------------------------------------------- identidade
const NAVY = "1B2A4A";
const BRANCO = "FFFFFF";
const TINTA = "16181D";
const MUDO = "5A5F6B";
const AZUL = "2A78D6";
const LARANJA = "EB6834";
const VERDE = "1E8C5A";
const VERDE_CLARO = "A8D5BF";
const TINTE = "EEF3FA";
const ACERTO = "D9E7F8";
const FALSO_POS = "ECEEF2";
const FALSO_NEG = "FBDFD2";
const TITULO_FONTE = "Cambria";
const CORPO_FONTE = "Calibri";

const L = 13.3;
const A = 7.5;
const MARGEM = 0.7;
const UTIL = L - 2 * MARGEM;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = GRUPO.nomes.length ? GRUPO.juntar(GRUPO.nomes) : "Grupo A2 — Mineração de Dados/KDD, UFG";
pres.title = "Triagem de cardiopatia pediátrica sem vazamento de dados";
pres.subject = "Mineração de Dados / KDD — Avaliação A2, Instituto de Informática, UFG";

pres.defineSlideMaster({
  title: "CLARO",
  background: { color: BRANCO },
  slideNumber: { x: L - 0.75, y: A - 0.45, fontFace: CORPO_FONTE, fontSize: 11, color: MUDO },
});
pres.defineSlideMaster({
  title: "ESCURO",
  background: { color: NAVY },
  slideNumber: { x: L - 0.75, y: A - 0.45, fontFace: CORPO_FONTE, fontSize: 11, color: "8A93A8" },
});

const texto = (slide, conteudo, opcoes) => slide.addText(conteudo, {
  isTextBox: true, margin: 0, fontFace: CORPO_FONTE, color: TINTA, ...opcoes,
});

const titulo = (slide, t, subtitulo) => {
  texto(slide, t, { x: MARGEM, y: 0.42, w: UTIL, h: 0.6, fontFace: TITULO_FONTE, fontSize: 30, bold: true });
  if (subtitulo) texto(slide, subtitulo, { x: MARGEM, y: 1.04, w: UTIL, h: 0.38, fontSize: 15, color: MUDO });
};

const estatistica = (slide, { x, y, w, valor, rotulo, cor = AZUL, corRotulo = MUDO, tamanho = 40, tamanhoRotulo = 14, hRotulo = 0.7 }) => {
  texto(slide, valor, { x, y, w, h: tamanho / 54, fontFace: TITULO_FONTE, fontSize: tamanho, bold: true, color: cor });
  texto(slide, rotulo, { x, y: y + tamanho / 54, w, h: hRotulo, fontSize: tamanhoRotulo, color: corRotulo, valign: "top" });
};

const circulo = (slide, { x, y, d = 0.46, marca, cor }) => {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: cor }, line: { color: cor } });
  texto(slide, marca, { x, y, w: d, h: d, align: "center", valign: "middle", fontFace: TITULO_FONTE, fontSize: 15, bold: true, color: BRANCO });
};

const cartao = (slide, { x, y, w, h, marca, titulo: t, texto: corpo, cor = AZUL, tamanhoTexto = 16 }) => {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: TINTE }, line: { color: TINTE } });
  circulo(slide, { x: x + 0.28, y: y + 0.28, marca, cor });
  texto(slide, t, { x: x + 0.86, y: y + 0.26, w: w - 1.14, h: 0.5, valign: "middle", fontFace: TITULO_FONTE, fontSize: 17, bold: true });
  texto(slide, corpo, { x: x + 0.3, y: y + 0.9, w: w - 0.6, h: h - 1.1, valign: "top", fontSize: tamanhoTexto, color: "3C4049" });
};

const faixa = (slide, t, { y = 6.05, h = 0.8 } = {}) => {
  slide.addShape(pres.ShapeType.roundRect, { x: MARGEM, y, w: UTIL, h, rectRadius: 0.06, fill: { color: NAVY }, line: { color: NAVY } });
  texto(slide, t, { x: MARGEM + 0.4, y, w: UTIL - 0.8, h, valign: "middle", fontFace: TITULO_FONTE, fontSize: 17, bold: true, color: BRANCO });
};

/** Gráfico de barras horizontais nativo, uma série, cor por barra. */
const barras = (slide, { x, y, w, h, rotulos, valores, cores, formato, min = 0, max, tamanho = 14 }) => {
  slide.addChart(pres.charts.BAR, [{ name: "valor", labels: rotulos, values: valores }], {
    x, y, w, h, barDir: "bar", barGapWidthPct: 45,
    chartColors: cores, showLegend: false, showTitle: false,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: formato,
    dataLabelFontFace: CORPO_FONTE, dataLabelFontSize: tamanho, dataLabelColor: TINTA,
    catAxisLabelFontFace: CORPO_FONTE, catAxisLabelFontSize: tamanho, catAxisLabelColor: TINTA,
    catAxisOrientation: "maxMin", catAxisLineShow: false,
    valAxisHidden: true, valAxisMinVal: min, valAxisMaxVal: max,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
  });
};

/** Matriz de confusão desenhada em formas: contagem e % da linha (classe real). */
const matriz = (slide, { x, y, m, rotulo }) => {
  const cab = 1.35, cw = 1.6, ch = 0.45, rh = 1.0;
  texto(slide, rotulo, { x, y, w: cab + 2 * cw, h: 0.45, align: "center", fontFace: TITULO_FONTE, fontSize: 18, bold: true });
  const y0 = y + 0.6;
  texto(slide, "real ↓   previsto →", { x, y: y0, w: cab, h: ch, valign: "middle", fontSize: 11, color: MUDO });
  ["Normal", "Anormal"].forEach((t, j) => texto(slide, t, {
    x: x + cab + j * cw, y: y0, w: cw, h: ch, align: "center", valign: "middle", fontSize: 14, bold: true, color: MUDO,
  }));
  [["Normal", [[m.tn, ACERTO], [m.fp, FALSO_POS]]], ["Anormal", [[m.fn, FALSO_NEG], [m.tp, ACERTO]]]].forEach(([t, celulas], i) => {
    const yy = y0 + ch + i * rh;
    texto(slide, t, { x, y: yy, w: cab - 0.15, h: rh, align: "right", valign: "middle", fontSize: 14, bold: true, color: MUDO });
    const total = celulas[0][0] + celulas[1][0];
    celulas.forEach(([v, cor], j) => {
      slide.addShape(pres.ShapeType.rect, {
        x: x + cab + j * cw + 0.03, y: yy + 0.03, w: cw - 0.06, h: rh - 0.06, fill: { color: cor }, line: { color: cor },
      });
      texto(slide, [
        { text: mil(v), options: { fontSize: 22, bold: true, color: cor === FALSO_NEG ? LARANJA : TINTA, breakLine: true } },
        { text: pct(v / total * 100), options: { fontSize: 13, color: MUDO } },
      ], { x: x + cab + j * cw, y: yy, w: cw, h: rh, align: "center", valign: "middle" });
    });
  });
  const sens = m.tp / (m.tp + m.fn);
  const esp = m.tn / (m.tn + m.fp);
  texto(slide, [
    { text: "sensibilidade ", options: { color: MUDO } }, { text: num(sens, 2), options: { bold: true } },
    { text: "   ·   especificidade ", options: { color: MUDO } }, { text: num(esp, 2), options: { bold: true } },
  ], { x, y: y0 + ch + 2 * rh + 0.15, w: cab + 2 * cw, h: 0.4, align: "center", fontSize: 16 });
};

const notas = (slide, quem, t) => slide.addNotes(`[${quem}] ${t}`);
const [P1, P2, P3] = GRUPO.nomes.length === 3 ? GRUPO.nomes : ["Integrante 1", "Integrante 2", "Integrante 3"];

const mt = INT.matriz_triagem;
const m05 = INT.matriz_05;

// ------------------------------------------------------------------- 1 capa
const s1 = pres.addSlide({ masterName: "ESCURO" });
texto(s1, "Triagem de cardiopatia pediátrica sem vazamento de dados", {
  x: MARGEM, y: 1.95, w: UTIL, h: 1.4, fontFace: TITULO_FONTE, fontSize: 40, bold: true, color: BRANCO,
});
texto(s1, "Estudo de caso UCMF — comparação de classificadores", {
  x: MARGEM, y: 3.45, w: UTIL, h: 0.5, fontSize: 21, color: "C3D0E8",
});
s1.addShape(pres.ShapeType.ellipse, { x: MARGEM, y: 4.33, w: 0.14, h: 0.14, fill: { color: LARANJA }, line: { color: LARANJA } });
texto(s1, "Mineração de Dados / KDD · Avaliação A2 · Instituto de Informática, UFG", {
  x: MARGEM + 0.34, y: 4.22, w: UTIL - 0.34, h: 0.36, fontSize: 14, color: "8A93A8",
});
texto(s1, GRUPO.linha("  ·  "), { x: MARGEM, y: 6.2, w: UTIL, h: 0.4, fontSize: 13, color: "8A93A8" });
notas(s1, P1, "Apresentação da A2, continuação da A1. Pergunta: dá para estimar o risco de cardiopatia antes da ausculta, sem trapacear com vazamento de dados? Divisão: problema e vazamento (slides 1–5); metodologia e resultados gerais (6–9); comparação, limiar, erros e conclusão (10–14).");

// ---------------------------------------------------------------- 2 problema
const s2 = pres.addSlide({ masterName: "CLARO" });
titulo(s2, "Dá para prever a cardiopatia antes da ausculta?",
  "Classificação binária supervisionada: Normal × Anormal, só com o que se sabe antes do exame do cardiologista");
estatistica(s2, { x: MARGEM, y: 1.85, w: 3.6, valor: mil(EDA.n), rotulo: "atendimentos (Real Hospital Português, 2003–2010)" });
estatistica(s2, { x: MARGEM + 4.0, y: 1.85, w: 3.6, valor: pct(EDA.pct_anormal), rotulo: "com patologia cardíaca", cor: LARANJA });
estatistica(s2, { x: MARGEM + 8.0, y: 1.85, w: 3.9, valor: String(EDA.atributos_modelo), rotulo: "atributos de antes da consulta" });
cartao(s2, {
  x: MARGEM, y: 3.75, w: 5.85, h: 1.95, marca: "?", cor: AZUL, titulo: "Por que importa",
  texto: `${pct(100 - EDA.pct_anormal)} das crianças encaminhadas são normais e ocupam a fila do especialista.`,
});
cartao(s2, {
  x: MARGEM + 6.05, y: 3.75, w: 5.85, h: 1.95, marca: "!", cor: LARANJA, titulo: "A armadilha",
  texto: "Algumas colunas registram o próprio exame que produz o diagnóstico: vazamento de dados.",
});
notas(s2, P1, `O conjunto tem ${mil(EDA.n)} atendimentos após a limpeza da A1. Os 13 atributos: encaminhamento (MOTIVO1, MOTIVO2, convênio), antropometria (peso, altura, IMC, idade, sexo), sinais vitais (FC, PA, PPA, pulsos) e sintomas (HDA). Um modelo de triagem ordenaria a fila por risco. O cuidado central: só usar o que existe antes da ausculta.`);

// ------------------------------------------------------- 3 vazamento de atributo
const s3 = pres.addSlide({ masterName: "CLARO" });
titulo(s3, "Vazamento de atributo: o sopro entrega o diagnóstico", "% de diagnósticos anormais conforme o achado de sopro na ausculta");
const sopros = [["Sistólico", LARANJA], ["Contínuo", LARANJA], ["Ausente", AZUL]];
barras(s3, {
  x: MARGEM, y: 1.65, w: 6.9, h: 3.6,
  rotulos: sopros.map(([k]) => `${k} (n = ${mil(EDA.sopro.prevalencia[k].n)})`),
  valores: sopros.map(([k]) => EDA.sopro.prevalencia[k].pct_anormal),
  cores: sopros.map(([, c]) => c), formato: '0.0"%"', max: 115, tamanho: 16,
});
estatistica(s3, {
  x: MARGEM + 7.5, y: 1.95, w: 4.4, valor: pct(EDA.sopro.oner.acuracia * 100), cor: LARANJA, tamanho: 54,
  rotulo: "de acerto com uma regra só: “sopro presente ⇒ anormal”", tamanhoRotulo: 16, hRotulo: 0.9,
});
faixa(s3, "SOPRO e B2 são achados da ausculta, o exame que gera o diagnóstico: ficam fora do modelo.");
notas(s3, P1, `Sem sopro, ${pct(EDA.sopro.prevalencia.Ausente.pct_anormal)} de anormais; com sopro sistólico, ${pct(EDA.sopro.prevalencia["Sistólico"].pct_anormal)}. Com o sopro, o modelo só copiaria a conclusão do médico. Categorias com menos de 10 casos (diastólico, sistólico e diastólico, não informado) foram omitidas do gráfico.`);

// ------------------------------------------------------- 4 auditoria de todos os atributos
const s4 = pres.addSlide({ masterName: "CLARO" });
titulo(s4, "Auditoria: nenhum outro atributo se aproxima do sopro", "AUC-ROC de cada atributo sozinho, fora da amostra (0,5 = acaso)");
const univ = Object.entries(EDA.auc_univariada).sort((a, b) => b[1].auc - a[1].auc);
const vazam = ["SOPRO", "B2"];
barras(s4, {
  x: MARGEM, y: 1.5, w: 7.3, h: 5.2,
  rotulos: univ.map(([k]) => nomeAtributo(k)), valores: univ.map(([, v]) => v.auc),
  cores: univ.map(([k]) => (vazam.includes(k) ? LARANJA : AZUL)), formato: "0.000", min: 0.5, max: 1.0, tamanho: 13,
});
estatistica(s4, {
  x: MARGEM + 7.9, y: 1.75, w: 4.0, valor: num(EDA.auc_univariada.SOPRO.auc), cor: LARANJA,
  rotulo: `SOPRO sozinho; o melhor atributo mantido (MOTIVO2) tem ${num(EDA.auc_univariada.MOTIVO2.auc)}`, hRotulo: 0.9,
});
texto(s4, [
  { text: "B2 sai pela origem, não pela força: ", options: { bold: true, breakLine: false } },
  { text: "também é achado da ausculta.", options: { breakLine: true } },
  { text: " ", options: { breakLine: true, fontSize: 8 } },
  { text: "MOTIVO1 e MOTIVO2 ficam: ", options: { bold: true } },
  { text: "registram o encaminhamento, anterior ao exame." },
], { x: MARGEM + 7.9, y: 3.6, w: 4.0, h: 2.2, fontSize: 16, color: "3C4049", valign: "top" });
notas(s4, P1, `Auditamos todos os atributos com dois critérios: existir antes do exame e não determinar o alvo. Só SOPRO e B2 caíram. "Sopro" em MOTIVO2 é a suspeita de quem encaminhou: ${EDA.motivo2_sopro.sem_sopro_confirmado} crianças não tiveram o sopro confirmado e ${pct(EDA.motivo2_sopro.pct_normal_sem_confirmacao)} delas eram normais.`);

// ---------------------------------------------- 5 vazamento de instância e de etapa
const s5 = pres.addSlide({ masterName: "CLARO" });
titulo(s5, "Dois vazamentos que não são colunas", "Ambos inflariam as métricas sem nenhum atributo suspeito no modelo");
cartao(s5, { x: MARGEM, y: 1.75, w: 5.85, h: 3.75, marca: "2", cor: AZUL, titulo: "De instância: a mesma criança volta", texto: "" });
estatistica(s5, {
  x: MARGEM + 0.3, y: 2.65, w: 5.25, valor: mil(EDA.retornos.pares_consecutivos), cor: AZUL, tamanho: 44,
  rotulo: `pares de retornos em IDs vizinhos; ao acaso seriam ${num(EDA.retornos.esperado_ao_acaso, 1)}`, tamanhoRotulo: 15, hRotulo: 0.5,
});
texto(s5, `Chave de paciente DN + sexo: ${mil(EDA.retornos.n_grupos)} crianças, cada uma inteira no treino ou no teste.`, {
  x: MARGEM + 0.3, y: 4.15, w: 5.25, h: 1.0, fontSize: 16, color: "3C4049", valign: "top",
});
cartao(s5, { x: MARGEM + 6.05, y: 1.75, w: 5.85, h: 3.75, marca: "3", cor: AZUL, titulo: "De pré-processamento", texto: "" });
[
  ["✗", LARANJA, "A1: ", "o CSV limpo foi imputado com medianas da base inteira, teste incluído."],
  ["✓", VERDE, "A2: ", "medianas, médias e frequências aprendidas só no treino de cada partição."],
].forEach(([marca, cor, rot, corpo], i) => {
  const yy = 2.75 + i * 1.25;
  circulo(s5, { x: MARGEM + 6.35, y: yy, d: 0.42, marca, cor });
  texto(s5, [{ text: rot, options: { bold: true } }, { text: corpo, options: { color: "3C4049" } }], {
    x: MARGEM + 6.95, y: yy - 0.04, w: 4.7, h: 1.0, fontSize: 16, valign: "top",
  });
});
faixa(s5, "Regra obrigatória: o algoritmo nunca pode examinar o conjunto de teste durante o aprendizado.");
notas(s5, P1, `O ID identifica o atendimento, não a criança. Também há ${EDA.retornos.grupos_mesmo_dia} grupos com mais de um registro no mesmo dia. A chave DN + sexo é conservadora: junta crianças nascidas no mesmo dia, o que só deixa a validação mais rígida.`);

// --------------------------------------------------------- 6 pré-processamento
const s6 = pres.addSlide({ masterName: "CLARO" });
titulo(s6, "Pré-processamento sem olhar o teste", "Regras fixas antes da partição; o que tem parâmetro é aprendido só no treino");
const passo = (slide, { x, y, w, h, marca, t, corpo, cor }) => {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: TINTE }, line: { color: TINTE } });
  circulo(slide, { x: x + 0.25, y: y + 0.25, marca, cor });
  texto(slide, t, { x: x + 0.82, y: y + 0.23, w: w - 0.95, h: 0.5, valign: "middle", fontFace: TITULO_FONTE, fontSize: 16, bold: true });
  texto(slide, corpo, { x: x + 0.25, y: y + 0.95, w: w - 0.5, h: h - 1.15, valign: "top", fontSize: 16, color: "3C4049" });
};
texto(s6, "Antes da partição", { x: MARGEM, y: 1.75, w: 2.6, h: 0.35, fontSize: 14, bold: true, color: MUDO });
passo(s6, { x: MARGEM, y: 2.2, w: 2.6, h: 3.2, marca: "1", cor: NAVY, t: "Limpeza da A1", corpo: "Sentinelas, faixas clínicas, datas e PPA. Regras fixas, iguais para todos." });
s6.addShape(pres.ShapeType.rightArrow, { x: 3.38, y: 3.6, w: 0.34, h: 0.4, fill: { color: MUDO }, line: { color: MUDO } });
s6.addShape(pres.ShapeType.roundRect, {
  x: 3.8, y: 1.62, w: 8.8, h: 3.98, rectRadius: 0.08, fill: { color: BRANCO }, line: { color: AZUL, width: 1.5, dashType: "dash" },
});
texto(s6, "Pipeline: ajustado só no treino de cada partição", { x: 4.1, y: 1.75, w: 8.2, h: 0.35, fontSize: 14, bold: true, color: AZUL });
[
  ["2", "Numéricas", "Mediana por sexo × faixa etária, indicador de ausência e z-score."],
  ["3", "Categóricas", "“Não informado” vira categoria; depois, one-hot."],
  ["4", "Convênio", `${EDA.convenio.categorias_antes} → ${EDA.convenio.categorias_depois} nomes; codificado pela frequência no treino.`],
].forEach(([marca, t, corpo], i) => passo(s6, { x: 4.1 + i * 2.85, y: 2.2, w: 2.6, h: 3.2, marca, t, corpo, cor: AZUL }));
faixa(s6, "Nenhuma mediana, média ou frequência é calculada com o conjunto de teste.");
notas(s6, P2, `A taxonomia da A1 (ausentes, duplicados, inconsistentes, atípicos) segue valendo; a limpeza é feita por regras fixas, por isso pode rodar antes da partição. Os passos 2 a 4 correm em paralelo dentro do pipeline. Sem reamostragem: ${pct(EDA.pct_anormal)} de anormais é desbalanceamento moderado, e o peso das classes vira hiperparâmetro. Convênio por frequência, e não por target encoding, para não usar o alvo.`);

// ------------------------------------------------------------- 7 protocolo
const s7 = pres.addSlide({ masterName: "CLARO" });
titulo(s7, "Validação cruzada aninhada, agrupada por paciente",
  "Regra prática da disciplina para 1.000 < N ≤ 100.000: validação cruzada estratificada com k = 10");
const bx = 1.2, bw = 1.0, bg = 0.1, by = 2.2, bh = 0.6;
texto(s7, "Laço externo (k = 10): estima o desempenho", { x: bx, y: 1.7, w: 6.0, h: 0.4, fontSize: 16, bold: true, color: NAVY });
const fimTreino = bx + 9 * (bw + bg) - bg;
s7.addShape(pres.ShapeType.rect, { x: bx, y: by, w: fimTreino - bx, h: bh, fill: { color: AZUL }, line: { color: AZUL } });
for (let i = 1; i < 9; i += 1) {
  s7.addShape(pres.ShapeType.line, { x: bx + i * (bw + bg) - bg / 2, y: by, w: 0, h: bh, line: { color: BRANCO, width: 2 } });
}
s7.addShape(pres.ShapeType.rect, { x: bx + 9 * (bw + bg), y: by, w: bw, h: bh, fill: { color: LARANJA }, line: { color: LARANJA } });
texto(s7, "treino (9 partes)", { x: bx, y: by + bh + 0.06, w: fimTreino - bx, h: 0.4, align: "center", valign: "top", fontSize: 16, bold: true, color: AZUL });
texto(s7, "teste", { x: bx + 9 * (bw + bg), y: by, w: bw, h: bh, align: "center", valign: "middle", fontSize: 16, bold: true, color: BRANCO });
const ix = 2.6, iw = 1.32, ig = 0.1, iy = 3.55, ih = 0.55;
const fimInterno = ix + 5 * iw + 4 * ig;
s7.addShape(pres.ShapeType.line, { x: bx, y: by + bh, w: ix - bx, h: iy - by - bh, line: { color: MUDO, width: 1.25, dashType: "dash" } });
s7.addShape(pres.ShapeType.line, { x: fimInterno, y: by + bh, w: fimTreino - fimInterno, h: iy - by - bh, flipH: true, line: { color: MUDO, width: 1.25, dashType: "dash" } });
for (let i = 0; i < 5; i += 1) {
  const cor = i < 4 ? VERDE : VERDE_CLARO;
  s7.addShape(pres.ShapeType.rect, { x: ix + i * (iw + ig), y: iy, w: iw, h: ih, fill: { color: cor }, line: { color: cor } });
}
texto(s7, [
  { text: "Laço interno (k = 5), só dentro do treino: ", options: { bold: true, color: VERDE } },
  { text: "escolhe os hiperparâmetros (por AUC-ROC) e o limiar de triagem" },
], { x: 1.2, y: iy + ih + 0.15, w: 10.9, h: 0.45, align: "center", fontSize: 16 });
[
  ["Agrupada", "as consultas da mesma criança ficam sempre na mesma parte"],
  ["Estratificada", `cerca de ${pct(EDA.pct_anormal, 0)} de anormais em cada parte`],
  ["Pareada", "as mesmas partições para os quatro modelos"],
].forEach(([t, corpo], i) => {
  const x = MARGEM + i * 4.0;
  s7.addShape(pres.ShapeType.ellipse, { x, y: 5.42, w: 0.16, h: 0.16, fill: { color: LARANJA }, line: { color: LARANJA } });
  texto(s7, [{ text: t, options: { bold: true, breakLine: true } }, { text: corpo, options: { color: "3C4049" } }], {
    x: x + 0.32, y: 5.3, w: 3.5, h: 1.0, fontSize: 15, valign: "top",
  });
});
notas(s7, P2, "StratifiedGroupKFold nos dois laços: estratifica pela classe e mantém cada criança inteira de um lado. O laço interno repete a busca em grade em cada uma das 10 rodadas, sem ver a parte de teste. Cada atendimento é testado exatamente uma vez, o que permite uma matriz de confusão agregada.");

// --------------------------------------------------- 8 algoritmos e métricas
const s8 = pres.addSlide({ masterName: "CLARO" });
titulo(s8, "Algoritmos e métricas", "Piso de referência: a classe majoritária (AUC-ROC = 0,5)");
cartao(s8, { x: MARGEM, y: 1.7, w: 3.85, h: 2.3, marca: "LR", cor: AZUL, titulo: "Logística", texto: "Baseline linear, regularização L2. Ajusta C e peso das classes." });
cartao(s8, { x: MARGEM + 4.025, y: 1.7, w: 3.85, h: 2.3, marca: "RF", cor: VERDE, titulo: "Random Forest", texto: "300 árvores. Ajusta profundidade e folha mínima." });
cartao(s8, { x: MARGEM + 8.05, y: 1.7, w: 3.85, h: 2.3, marca: "GB", cor: LARANJA, titulo: "Gradient Boosting", texto: "Histogramas e parada antecipada. Ajusta taxa, folhas e L2." });
estatistica(s8, {
  x: MARGEM, y: 4.5, w: 5.6, valor: "AUC-ROC", cor: NAVY,
  rotulo: "escolhe os hiperparâmetros; também medimos AUC-PR, sensibilidade, especificidade, precisão e F1", tamanhoRotulo: 16, hRotulo: 1.0,
});
estatistica(s8, {
  x: MARGEM + 6.3, y: 4.5, w: 5.6, valor: "Sensibilidade ≥ 0,90", cor: LARANJA,
  rotulo: "define o limiar de triagem, escolhido com as previsões do próprio treino", tamanhoRotulo: 16, hRotulo: 1.0,
});
notas(s8, P2, `O piso prevê sempre a prevalência do treino: AUC 0,5 e AUC-PR ${num(media("dummy", "auc_pr"))}. Classe positiva: Anormal. Acurácia sozinha não basta porque as classes não são equilibradas. O limiar de triagem é escolhido sem ver o teste, com previsões fora da dobra do laço interno.`);

// ---------------------------------------------------------------- 9 resultados
const s9 = pres.addSlide({ masterName: "CLARO" });
titulo(s9, "Os três superam o piso; os ensembles lideram", "AUC-ROC média nas 10 partições externas (± desvio-padrão)");
[
  ["dummy", "Piso de referência", "8A93A8"], ["logistica", "Regressão Logística", AZUL],
  ["random_forest", "Random Forest", VERDE], ["gradient_boosting", "Gradient Boosting", LARANJA],
].forEach(([m, rot, cor], i) => {
  const r = NI[m].resumo.limiar_05;
  estatistica(s9, {
    x: MARGEM + i * 3.0, y: 1.8, w: 2.8, valor: num(r.auc_roc.media), cor, tamanho: 48,
    rotulo: `${rot}\n± ${num(r.auc_roc.dp)}`, tamanhoRotulo: 15, hRotulo: 0.8,
  });
});
const linhas9 = [["Limiar 0,5", "LR", "RF", "GB"]].concat(
  [["AUC-PR", "auc_pr"], ["Acurácia balanceada", "acuracia_balanceada"], ["Sensibilidade", "sensibilidade"],
    ["Especificidade", "especificidade"]].map(([rot, k]) =>
    [rot, num(media("logistica", k)), num(media("random_forest", k)), num(media("gradient_boosting", k))]));
s9.addTable(linhas9.map((l, i) => l.map((c) => ({
  text: c, options: { bold: i === 0, color: i === 0 ? BRANCO : TINTA, fill: { color: i === 0 ? NAVY : (i % 2 ? TINTE : BRANCO) } },
}))), {
  x: MARGEM + 1.5, y: 3.95, w: UTIL - 3.0, colW: [3.9, 1.9, 1.9, 1.9],
  fontFace: CORPO_FONTE, fontSize: 16, align: "center", valign: "middle", rowH: 0.44,
  border: { type: "none" },
});
notas(s9, P2, `Gradient Boosting com a maior AUC-ROC (${num(media("gradient_boosting", "auc_roc"))}), Random Forest logo atrás (${num(media("random_forest", "auc_roc"))}) e a logística com ${num(media("logistica", "auc_roc"))}. F1 no limiar 0,5: LR ${num(media("logistica", "f1"))}, RF ${num(media("random_forest", "f1"))}, GB ${num(media("gradient_boosting", "f1"))}. Atenção: no limiar 0,5 a sensibilidade fica perto de 0,63 em todos, inadequada para triagem — é o gancho para o slide do limiar.`);

// --------------------------------------------------------------- 10 teste
const s10 = pres.addSlide({ masterName: "CLARO" });
titulo(s10, "A diferença é real, mas pequena", "Teste t 5×2cv de Dietterich com correção de Holm (α = 0,05), na AUC-ROC");
const pares = [["logistica", "random_forest", "LR × RF"], ["logistica", "gradient_boosting", "LR × GB"], ["random_forest", "gradient_boosting", "RF × GB"]];
const tab = [["Par", "Δ AUC", "p (Holm)", "Resultado"]].concat(pares.map(([a, b, rot]) => {
  const p = par(a, b).auc_roc;
  return [rot, num(p.dif_media), num(p.p_holm), p.p_holm < 0.05 ? "diferença significativa" : "sem diferença significativa"];
}));
s10.addTable(tab.map((l, i) => l.map((c, j) => {
  const sig = i > 0 && j >= 2 && Number(tab[i][2].replace(",", ".")) < 0.05;
  return {
    text: c,
    options: { bold: i === 0 || sig, color: i === 0 ? BRANCO : (sig ? LARANJA : TINTA), fill: { color: i === 0 ? NAVY : (i % 2 ? TINTE : BRANCO) } },
  };
})), {
  x: MARGEM + 0.6, y: 1.85, w: UTIL - 1.2, colW: [2.2, 2.0, 2.0, 4.5],
  fontFace: CORPO_FONTE, fontSize: 20, align: "center", valign: "middle", rowH: 0.66,
  border: { type: "none" },
});
estatistica(s10, {
  x: MARGEM + 0.6, y: 4.65, w: 10.7, valor: `≈ ${num(Math.abs(par("logistica", "gradient_boosting").auc_roc.dif_media), 2)} de AUC`, cor: LARANJA, tamanho: 30,
  rotulo: "é toda a vantagem dos ensembles sobre a logística", tamanhoRotulo: 16, hRotulo: 0.5,
});
faixa(s10, "Três algoritmos no mesmo patamar: o limite parece estar na informação, não no algoritmo.");
notas(s10, P3, `Média de métricas não basta para declarar superioridade: as 10 partições compartilham treino. Para um único dataset, os slides recomendam o 5×2cv de Dietterich, que controla melhor o erro Tipo I; Holm corrige as três comparações. RF × GB: não rejeitar H0 não prova igualdade — dizemos "sem diferença significativa". Na taxa de erro (limiar 0,5), nenhum par difere (p de Holm entre ${num(Math.min(...pares.map(([a, b]) => par(a, b).erro.p_holm)))} e ${num(Math.max(...pares.map(([a, b]) => par(a, b).erro.p_holm)))}).`);

// -------------------------------------------------------------- 11 limiar
const s11 = pres.addSlide({ masterName: "CLARO" });
titulo(s11, "O limiar decide se o modelo serve para triagem", "Matrizes de confusão do Gradient Boosting, somadas nas 10 partições de teste");
matriz(s11, { x: 0.9, y: 1.6, m: m05, rotulo: "Limiar 0,5" });
matriz(s11, { x: 7.75, y: 1.6, m: mt, rotulo: "Limiar de triagem" });
s11.addShape(pres.ShapeType.rightArrow, { x: 6.0, y: 3.3, w: 1.2, h: 0.55, fill: { color: MUDO }, line: { color: MUDO } });
texto(s11, "baixar o limiar", { x: 5.65, y: 3.95, w: 1.9, h: 0.35, align: "center", fontSize: 13, color: MUDO });
faixa(s11, `Dispensaria ${pct(mt.tn / (mt.tn + mt.fp) * 100, 0)} das crianças normais e deixaria passar ${pct(mt.fn / (mt.fn + mt.tp) * 100, 0)} das cardiopatias: prioriza a fila, não substitui o especialista.`, { h: 0.9 });
notas(s11, P3, `Linhas: classe real; colunas: previsão. Em laranja, os falsos negativos — o erro grave na triagem. No limiar 0,5 o modelo perderia mais de um terço das cardiopatias. O limiar de triagem ficou entre ${num(Math.min(...NI.gradient_boosting.folds.map((f) => f.limiar_triagem)), 2)} e ${num(Math.max(...NI.gradient_boosting.folds.map((f) => f.limiar_triagem)), 2)}, escolhido no treino de cada partição; a sensibilidade no teste variou de ${num(Math.min(...NI.gradient_boosting.folds.map((f) => f.metricas_triagem.sensibilidade)), 2)} a ${num(Math.max(...NI.gradient_boosting.folds.map((f) => f.metricas_triagem.sensibilidade)), 2)}. As curvas ROC e PR estão na Fig. 3 do artigo.`);

// ---------------------------------------------------------------- 12 erros
const s12 = pres.addSlide({ masterName: "CLARO" });
titulo(s12, "Onde o modelo ainda erra", "Cardiopatias que escapam no limiar de triagem (% dos anormais de cada grupo)");
texto(s12, "Por motivo do encaminhamento", { x: MARGEM, y: 1.65, w: 6.0, h: 0.35, fontSize: 15, bold: true, color: MUDO });
[
  ["5 - Parecer cardiológico", "Parecer cardiológico", LARANJA], ["2 - Check-up", "Check-up", LARANJA],
  ["6 - Suspeita de cardiopatia", "Suspeita de cardiopatia", AZUL], ["1 - Cardiopatia já estabelecida", "Cardiopatia estabelecida", AZUL],
].forEach(([chave, rot, cor], i) => estatistica(s12, {
  x: MARGEM + i * 3.0, y: 2.05, w: 2.85, tamanho: 44, cor, valor: pct(fn("perfil_fn_triagem", "motivo1", chave), 0), rotulo: rot, tamanhoRotulo: 15,
}));
texto(s12, "Pelo sopro (que o modelo não vê)", { x: MARGEM, y: 3.75, w: 6.0, h: 0.35, fontSize: 15, bold: true, color: MUDO });
[["sem sopro", "sem sopro", LARANJA], ["com sopro", "com sopro", AZUL]].forEach(([chave, rot, cor], i) => estatistica(s12, {
  x: MARGEM + i * 3.0, y: 4.15, w: 2.85, tamanho: 44, cor, valor: pct(fn("perfil_fn_triagem", "sopro", chave), 0), rotulo: rot, tamanhoRotulo: 15,
}));
faixa(s12, "Erra nos encaminhamentos de rotina e nas cardiopatias sem sopro: a ausculta segue indispensável.");
notas(s12, P3, `Os erros não são aleatórios: o modelo acerta quando quem encaminhou já suspeitava e erra no parecer pré-operatório e no check-up. No limiar 0,5 (números do artigo), escapam ${pct(fn("perfil_fn_05", "sopro", "sem sopro"), 1)} das cardiopatias sem sopro, contra ${pct(fn("perfil_fn_05", "sopro", "com sopro"), 1)} das com sopro. O erro também cresce com a idade: no limiar 0,5, escapam ${pct(fn("perfil_fn_05", "faixa_etaria", "Lactente"), 0)} dos lactentes anormais e ${pct(fn("perfil_fn_05", "faixa_etaria", "Adolescente"), 0)} dos adolescentes.`);

// ----------------------------------------------------------- 13 importância
const s13 = pres.addSlide({ masterName: "CLARO" });
titulo(s13, "O que o modelo aprendeu", "Queda da AUC-ROC ao embaralhar cada atributo (Gradient Boosting; os 8 mais importantes)");
const imp = INT.importancia.gradient_boosting;
const top = Object.keys(imp).slice(0, 8);
barras(s13, {
  x: MARGEM, y: 1.55, w: 7.4, h: 4.3,
  rotulos: top.map(nomeAtributo), valores: top.map((k) => imp[k].media),
  cores: top.map((_, i) => (i === 0 ? LARANJA : AZUL)), formato: "0.000", max: imp[top[0]].media * 1.2, tamanho: 15,
});
texto(s13, [
  { text: `Embaralhar o ${top[0]} derruba a AUC em ${num(imp[top[0]].media)}: `, options: { bold: true } },
  { text: `mais de ${Math.floor(imp[top[0]].media / imp[top[1]].media)} vezes o efeito do segundo atributo (${nomeAtributo(top[1])}).`, options: { color: "3C4049" } },
], { x: MARGEM + 8.0, y: 2.0, w: 3.9, h: 2.4, fontSize: 18, valign: "top" });
faixa(s13, "O modelo aprende a suspeita de quem encaminhou, refinada por FC e sintomas.");
const or = INT.logistica.coeficientes;
notas(s13, P3, `MOTIVO2 é o motivo detalhado do encaminhamento. Na logística, o maior efeito positivo é o encaminhamento por sopro: e^β = ${num(or["cat__MOTIVO2_6 - Sopro"].razao_de_chance, 2)} (efeito relativo: one-hot completo e regularização, sem categoria de referência). Cardiopatia já estabelecida: ${num(or["cat__MOTIVO1_1 - Cardiopatia já estabelecida"].razao_de_chance, 2)}; check-up puxa para baixo (${num(or["cat__MOTIVO1_2 - Check-up"].razao_de_chance, 2)}). Medidas antropométricas correlacionadas dividem a importância entre si.`);

// -------------------------------------------------------------- 14 conclusão
const s14 = pres.addSlide({ masterName: "ESCURO" });
texto(s14, "Conclusão", { x: MARGEM, y: 0.55, w: UTIL, h: 0.7, fontFace: TITULO_FONTE, fontSize: 32, bold: true, color: BRANCO });
[
  ["Resultado", `Sem vazamento, AUC-ROC de ${num(media("gradient_boosting", "auc_roc"))}. Na triagem, ${pct(mt.tp / (mt.tp + mt.fn) * 100, 0)} de sensibilidade com especificidade de ${num(media("gradient_boosting", "especificidade", "triagem"), 2)}.`],
  ["Uso", "Prioriza a fila do especialista; não substitui a ausculta."],
  ["Limitações", "Um hospital, quase tudo de 2003–2010; chave de paciente aproximada; erra mais sem sopro."],
  ["Próximos passos", "Validação temporal, calibração e limiar pelos custos clínicos."],
].forEach(([t, corpo], i) => {
  texto(s14, t, { x: MARGEM, y: 1.6 + i * 1.08, w: 3.0, h: 0.9, valign: "top", fontFace: TITULO_FONTE, fontSize: 20, bold: true, color: LARANJA });
  texto(s14, corpo, { x: MARGEM + 3.1, y: 1.6 + i * 1.08, w: UTIL - 3.1, h: 0.9, valign: "top", fontSize: 19, color: "E6ECF7" });
});
texto(s14, "Obrigado. Perguntas?", { x: MARGEM, y: 6.05, w: UTIL, h: 0.6, fontFace: TITULO_FONTE, fontSize: 24, bold: true, color: BRANCO });
notas(s14, P3, `Sem os casos de cardiopatia já estabelecida, a AUC agregada cai pouco, para ${num(INT.sem_cardiopatia_estabelecida.auc_roc)}: o modelo não depende só dos casos óbvios. A prevalência de anormais cai ao longo dos anos, por isso a validação temporal é o próximo passo. Código e resultados no repositório citado no rodapé do artigo, com random_state = 42. Fonocardiograma digital na triagem é outra extensão possível.`);

const destino = path.join(RAIZ, "slides", "Apresentacao_A2.pptx");
fs.mkdirSync(path.dirname(destino), { recursive: true });
// O pptxgenjs grava entradas de pasta no ZIP; alguns serviços de nuvem (Drive,
// OneDrive) recusam abrir o arquivo por isso. Regrava só com os arquivos.
const JSZip = require("jszip");
pres.write({ outputType: "nodebuffer" }).then(async (bruto) => {
  const origem = await JSZip.loadAsync(bruto);
  const limpo = new JSZip();
  for (const [nome, arquivo] of Object.entries(origem.files)) {
    if (!arquivo.dir) limpo.file(nome, await arquivo.async("nodebuffer"), { createFolders: false });
  }
  fs.writeFileSync(destino, await limpo.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  console.log(`Gravado: ${destino}`);
});
