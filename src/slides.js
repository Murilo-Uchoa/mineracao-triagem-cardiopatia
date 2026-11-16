/**
 * Gera a apresentação de 15 min da A2, no mesmo sistema visual da A1.
 *
 *   node src/slides.js
 *
 * Enunciado: 15 min, ênfase em metodologia e resultados; slides padronizados,
 * numerados, com pouco texto e elementos legíveis. Treze slides — cerca de
 * 70 s cada. Todos os números vêm de resultados/*.json.
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

// --------------------------------------------------------------- identidade
const NAVY = "1B2A4A";
const BRANCO = "FFFFFF";
const TINTA = "16181D";
const MUDO = "5A5F6B";
const AZUL = "2A78D6";
const LARANJA = "EB6834";
const VERDE = "1E8C5A";
const TINTE = "EEF3FA";
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

const titulo = (slide, texto, subtitulo) => {
  slide.addText(texto, {
    x: MARGEM, y: 0.42, w: UTIL, h: 0.6, isTextBox: true, margin: 0,
    fontFace: TITULO_FONTE, fontSize: 30, bold: true, color: TINTA,
  });
  if (subtitulo) {
    slide.addText(subtitulo, {
      x: MARGEM, y: 1.04, w: UTIL, h: 0.38, isTextBox: true, margin: 0,
      fontFace: CORPO_FONTE, fontSize: 15, color: MUDO,
    });
  }
};

const estatistica = (slide, { x, y, w, valor, rotulo, cor = AZUL, corRotulo = MUDO, tamanho = 40 }) => {
  slide.addText(valor, {
    x, y, w, h: 0.74, isTextBox: true, margin: 0,
    fontFace: TITULO_FONTE, fontSize: tamanho, bold: true, color: cor,
  });
  slide.addText(rotulo, {
    x, y: y + 0.74, w, h: 0.6, isTextBox: true, margin: 0,
    fontFace: CORPO_FONTE, fontSize: 13, color: corRotulo, valign: "top",
  });
};

const cartao = (slide, { x, y, w, h, marca, titulo: t, texto, cor = AZUL, tamanhoTexto = 14 }) => {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08, fill: { color: TINTE }, line: { color: TINTE },
  });
  slide.addShape(pres.ShapeType.ellipse, {
    x: x + 0.28, y: y + 0.28, w: 0.46, h: 0.46, fill: { color: cor }, line: { color: cor },
  });
  slide.addText(marca, {
    x: x + 0.28, y: y + 0.28, w: 0.46, h: 0.46, isTextBox: true, margin: 0,
    align: "center", valign: "middle", fontFace: TITULO_FONTE, fontSize: 15, bold: true, color: BRANCO,
  });
  slide.addText(t, {
    x: x + 0.86, y: y + 0.26, w: w - 1.14, h: 0.5, isTextBox: true, margin: 0,
    valign: "middle", fontFace: TITULO_FONTE, fontSize: 17, bold: true, color: TINTA,
  });
  slide.addText(texto, {
    x: x + 0.3, y: y + 0.86, w: w - 0.6, h: h - 1.08, isTextBox: true, margin: 0,
    valign: "top", fontFace: CORPO_FONTE, fontSize: tamanhoTexto, color: "3C4049",
  });
};

const faixa = (slide, texto, { y = 6.15, h = 0.8 } = {}) => {
  slide.addShape(pres.ShapeType.roundRect, {
    x: MARGEM, y, w: UTIL, h, rectRadius: 0.06, fill: { color: NAVY }, line: { color: NAVY },
  });
  slide.addText(texto, {
    x: MARGEM + 0.4, y, w: UTIL - 0.8, h, isTextBox: true, margin: 0, valign: "middle",
    fontFace: TITULO_FONTE, fontSize: 17, bold: true, color: BRANCO,
  });
};

/** Dimensões de um PNG lidas do cabeçalho, para preservar a proporção. */
const proporcao = (arquivo) => {
  const b = fs.readFileSync(path.join(RAIZ, "figuras", arquivo));
  return b.readUInt32BE(20) / b.readUInt32BE(16);
};

const figura = (slide, arquivo, { x, y, wMax, hMax }) => {
  const asp = proporcao(arquivo);
  let w = wMax;
  let h = w * asp;
  if (h > hMax) { h = hMax; w = h / asp; }
  slide.addImage({ path: path.join(RAIZ, "figuras", arquivo), x: x + (wMax - w) / 2, y, w, h });
};

const notas = (slide, quem, texto) => slide.addNotes(`[${quem}] ${texto}`);
const [P1, P2, P3] = GRUPO.nomes.length === 3 ? GRUPO.nomes : ["Integrante 1", "Integrante 2", "Integrante 3"];

// ------------------------------------------------------------------- 1 capa
const s1 = pres.addSlide({ masterName: "ESCURO" });
s1.addText("Triagem de cardiopatia pediátrica sem vazamento de dados", {
  x: MARGEM, y: 1.95, w: UTIL, h: 1.4, isTextBox: true, margin: 0,
  fontFace: TITULO_FONTE, fontSize: 40, bold: true, color: BRANCO,
});
s1.addText("Estudo de caso UCMF — comparação de classificadores", {
  x: MARGEM, y: 3.45, w: UTIL, h: 0.5, isTextBox: true, margin: 0,
  fontFace: CORPO_FONTE, fontSize: 21, color: "C3D0E8",
});
s1.addShape(pres.ShapeType.ellipse, {
  x: MARGEM, y: 4.33, w: 0.14, h: 0.14, fill: { color: LARANJA }, line: { color: LARANJA },
});
s1.addText("Mineração de Dados / KDD · Avaliação A2 · Instituto de Informática, UFG", {
  x: MARGEM + 0.34, y: 4.22, w: UTIL - 0.34, h: 0.36, isTextBox: true, margin: 0,
  fontFace: CORPO_FONTE, fontSize: 14, color: "8A93A8",
});
s1.addText(GRUPO.linha("  ·  "), {
  x: MARGEM, y: 6.2, w: UTIL, h: 0.4, isTextBox: true, margin: 0,
  fontFace: CORPO_FONTE, fontSize: 13, color: "8A93A8",
});
notas(s1, P1, "Apresentação da A2, continuação da A1. Pergunta: dá para estimar o risco de cardiopatia antes da ausculta, sem trapacear com vazamento de dados? Divisão: problema e vazamento; metodologia; resultados.");

// ---------------------------------------------------------------- 2 problema
const s2 = pres.addSlide({ masterName: "CLARO" });
titulo(s2, "Dá para prever a cardiopatia antes da ausculta?",
  "Classificação binária supervisionada: Normal × Anormal, com o que se sabe antes do exame do cardiologista");
estatistica(s2, { x: MARGEM, y: 1.85, w: 3.6, valor: mil(EDA.n), rotulo: "atendimentos (Real Hospital Português, 2003–2010)" });
estatistica(s2, { x: MARGEM + 4.0, y: 1.85, w: 3.6, valor: pct(EDA.pct_anormal), rotulo: "com patologia cardíaca", cor: LARANJA });
estatistica(s2, { x: MARGEM + 8.0, y: 1.85, w: 3.9, valor: String(EDA.atributos_modelo), rotulo: "atributos: encaminhamento, antropometria, sinais vitais, sintomas" });
cartao(s2, {
  x: MARGEM, y: 3.75, w: 5.85, h: 2.05, marca: "?", cor: AZUL, titulo: "Por que importa",
  texto: `${pct(100 - EDA.pct_anormal)} das crianças encaminhadas são normais e ocupam a fila do especialista.`,
});
cartao(s2, {
  x: MARGEM + 6.05, y: 3.75, w: 5.85, h: 2.05, marca: "!", cor: LARANJA, titulo: "A armadilha",
  texto: "Algumas variáveis registram o próprio exame que produz o diagnóstico: vazamento de dados.",
});
notas(s2, P1, `O conjunto tem ${mil(EDA.n)} atendimentos após a limpeza da A1. Um modelo de triagem ordenaria a fila por risco. O cuidado central: só usar o que existe antes da ausculta.`);

// ------------------------------------------------------- 3 vazamento de atributo
const s3 = pres.addSlide({ masterName: "CLARO" });
titulo(s3, "Vazamento de atributo: o sopro carrega o diagnóstico");
figura(s3, "fig1_eda.png", { x: MARGEM, y: 1.15, wMax: 6.3, hMax: 6.0 });
estatistica(s3, {
  x: MARGEM + 6.8, y: 1.6, w: 5.1, valor: pct(EDA.sopro.oner.acuracia * 100), cor: LARANJA,
  rotulo: "de acerto com uma única regra: “sopro presente ⇒ anormal”",
});
estatistica(s3, {
  x: MARGEM + 6.8, y: 3.15, w: 5.1, valor: num(EDA.auc_univariada.SOPRO.auc), cor: LARANJA,
  rotulo: `AUC do SOPRO isolado, contra ${num(EDA.auc_univariada.MOTIVO2.auc)} do melhor atributo mantido`,
});
s3.addText([
  { text: "SOPRO e B2 excluídos: ", options: { bold: true, color: TINTA } },
  { text: "achados da ausculta. MOTIVO1 e MOTIVO2 ficam: são o encaminhamento, anterior ao exame." },
], {
  x: MARGEM + 6.8, y: 4.75, w: 5.1, h: 1.2, isTextBox: true, margin: 0,
  fontFace: CORPO_FONTE, fontSize: 15, color: "3C4049", valign: "top",
});
notas(s3, P1, `Sem sopro, ${pct(EDA.sopro.prevalencia.Ausente.pct_anormal)} de anormais; com sopro sistólico, ${pct(EDA.sopro.prevalencia["Sistólico"].pct_anormal)}. Auditamos todos os atributos com dois critérios: existir antes do exame e não determinar o alvo. Só SOPRO e B2 caíram. "Sopro" em MOTIVO2 é a suspeita de quem encaminhou: ${EDA.motivo2_sopro.sem_sopro_confirmado} crianças não tiveram o sopro confirmado e ${pct(EDA.motivo2_sopro.pct_normal_sem_confirmacao)} delas eram normais.`);

// ---------------------------------------------- 4 vazamento de instância e de etapa
const s4 = pres.addSlide({ masterName: "CLARO" });
titulo(s4, "Dois vazamentos que não são atributos", "Ambos poderiam inflar as métricas sem que nenhuma coluna suspeita fosse usada");
cartao(s4, {
  x: MARGEM, y: 1.75, w: 5.85, h: 3.6, marca: "2", cor: AZUL, titulo: "De instância: a mesma criança volta",
  texto: `${mil(EDA.retornos.pares_consecutivos)} pares de IDs seguidos com a mesma data de nascimento e sexo — ao acaso seriam ${num(EDA.retornos.esperado_ao_acaso, 1)}.\n\nChave de paciente DN + sexo: ${mil(EDA.retornos.n_grupos)} grupos, nunca divididos entre treino e teste.`,
});
cartao(s4, {
  x: MARGEM + 6.05, y: 1.75, w: 5.85, h: 3.6, marca: "3", cor: AZUL, titulo: "De pré-processamento",
  texto: "O CSV limpo da A1 trazia medianas calculadas na base inteira.\n\nA imputação foi refeita dentro de cada partição de treino.",
});
faixa(s4, "Regra obrigatória: o algoritmo nunca pode examinar o conjunto de teste durante o aprendizado.", { y: 5.75 });
notas(s4, P1, `O ID identifica o atendimento, não a criança. Também há ${EDA.retornos.grupos_mesmo_dia} grupos com mais de um registro no mesmo dia. A chave DN + sexo é conservadora: junta crianças nascidas no mesmo dia, o que só deixa a validação mais rígida.`);

// --------------------------------------------------------- 5 pré-processamento
const s5 = pres.addSlide({ masterName: "CLARO" });
titulo(s5, "Pré-processamento sem olhar o teste", "Limpeza fixa antes da partição; tudo o que tem parâmetro, ajustado só no treino");
const passos = [
  ["1", "Limpeza da A1", "Sentinelas, faixas clínicas, datas, PPA reconstruída. Regras fixas: rodam antes.", NAVY],
  ["2", "Numéricas", "Mediana por sexo × faixa etária + indicador de ausência → z-score.", AZUL],
  ["3", "Categóricas", "“Não informado” explícito → one-hot.", AZUL],
  ["4", "Convênio", `${EDA.convenio.categorias_antes} → ${EDA.convenio.categorias_depois} categorias; frequência no treino, sem target encoding.`, AZUL],
];
passos.forEach(([marca, t, texto, cor], i) => {
  cartao(s5, { x: MARGEM + (i % 2) * 6.05, y: 1.7 + Math.floor(i / 2) * 2.2, w: 5.85, h: 2.0, marca, titulo: t, texto, cor });
});
faixa(s5, "Sem reamostragem: 42,6% de anormais é desbalanceamento moderado; o peso das classes vira hiperparâmetro.", { y: 6.2, h: 0.75 });
notas(s5, P2, "A taxonomia da A1 (ausentes, duplicados, inconsistentes, atípicos) segue valendo. A diferença: medianas, médias, desvios e frequências agora são aprendidos dentro do pipeline, no treino de cada partição.");

// ------------------------------------------------------------- 6 protocolo
const s6 = pres.addSlide({ masterName: "CLARO" });
titulo(s6, "Validação cruzada aninhada, agrupada por paciente",
  "Regra prática da disciplina para 1.000 < N ≤ 100.000: validação cruzada estratificada com k = 10");
figura(s6, "fig2_metodologia.png", { x: MARGEM, y: 1.65, wMax: UTIL, hMax: 3.9 });
s6.addText([
  { text: "Laço externo (10): ", options: { bold: true } }, { text: "estima o desempenho.   " },
  { text: "Laço interno (5): ", options: { bold: true } }, { text: "escolhe hiperparâmetros por AUC-ROC.   " },
  { text: "Mesmas partições ", options: { bold: true } }, { text: "para todos os modelos." },
], {
  x: MARGEM, y: 5.75, w: UTIL, h: 0.9, isTextBox: true, margin: 0,
  fontFace: CORPO_FONTE, fontSize: 15, color: "3C4049",
});
notas(s6, P2, "StratifiedGroupKFold nos dois laços: estratifica pela classe e mantém cada criança inteira de um lado. Cada atendimento é avaliado exatamente uma vez, o que permite uma matriz de confusão agregada.");

// --------------------------------------------------- 7 algoritmos e métricas
const s7 = pres.addSlide({ masterName: "CLARO" });
titulo(s7, "Algoritmos e métricas", "Um baseline simples, dois modelos mais complexos e um piso de referência");
cartao(s7, { x: MARGEM, y: 1.7, w: 3.85, h: 2.3, marca: "LR", cor: AZUL, titulo: "Logística", texto: "Baseline linear com L2; C e peso de classe ajustados." });
cartao(s7, { x: MARGEM + 4.025, y: 1.7, w: 3.85, h: 2.3, marca: "RF", cor: VERDE, titulo: "Random Forest", texto: "300 árvores; profundidade e folha mínima ajustadas." });
cartao(s7, { x: MARGEM + 8.05, y: 1.7, w: 3.85, h: 2.3, marca: "GB", cor: LARANJA, titulo: "Gradient Boosting", texto: "Histogramas, parada antecipada; taxa, folhas e L2 ajustadas." });
cartao(s7, {
  x: MARGEM, y: 4.2, w: UTIL, h: 1.75, marca: "%", cor: NAVY, titulo: "Métricas (classe positiva: Anormal)",
  texto: "AUC-ROC (critério de escolha) · AUC-PR · acurácia balanceada · sensibilidade · especificidade · precisão · F1. Acurácia não basta.",
});
faixa(s7, "Limiar de triagem: sensibilidade ≥ 0,90, escolhido nas previsões do próprio treino.", { y: 6.15, h: 0.75 });
notas(s7, P2, "O piso de referência prevê sempre a prevalência: AUC 0,5 e AUC-PR 0,426. O limiar de triagem é escolhido sem ver o teste, com previsões fora da dobra do treino externo.");

// ---------------------------------------------------------------- 8 resultados
const s8 = pres.addSlide({ masterName: "CLARO" });
titulo(s8, "Os três superam o piso; os ensembles lideram", "AUC-ROC média nas 10 partições externas (± desvio-padrão)");
const colunas = [
  ["dummy", "Piso de referência", "8A93A8"], ["logistica", "Regressão Logística", AZUL],
  ["random_forest", "Random Forest", VERDE], ["gradient_boosting", "Gradient Boosting", LARANJA],
];
colunas.forEach(([m, rot, cor], i) => {
  const r = NI[m].resumo.limiar_05;
  estatistica(s8, {
    x: MARGEM + i * 3.0, y: 1.85, w: 2.8, valor: num(r.auc_roc.media), cor, tamanho: 44,
    rotulo: `${rot}\n± ${num(r.auc_roc.dp)} · AUC-PR ${num(r.auc_pr.media)}`,
  });
});
const linhas = [["Métrica (limiar 0,5)", "LR", "RF", "GB"]].concat(
  [["Acurácia balanceada", "acuracia_balanceada"], ["Sensibilidade", "sensibilidade"],
    ["Especificidade", "especificidade"], ["F1", "f1"]].map(([rot, k]) =>
    [rot, num(media("logistica", k)), num(media("random_forest", k)), num(media("gradient_boosting", k))]));
s8.addTable(linhas.map((l, i) => l.map((c) => ({
  text: c, options: { bold: i === 0, color: i === 0 ? BRANCO : TINTA, fill: { color: i === 0 ? NAVY : (i % 2 ? TINTE : BRANCO) } },
}))), {
  x: MARGEM + 1.5, y: 3.85, w: UTIL - 3.0, colW: [3.9, 1.9, 1.9, 1.9],
  fontFace: CORPO_FONTE, fontSize: 15, align: "center", valign: "middle", rowH: 0.42,
  border: { type: "none" },
});
notas(s8, P3, `Gradient Boosting com a maior AUC-ROC (${num(media("gradient_boosting", "auc_roc"))}), Random Forest logo atrás (${num(media("random_forest", "auc_roc"))}) e a logística com ${num(media("logistica", "auc_roc"))}. No limiar 0,5, a sensibilidade fica perto de 0,63 em todos: inadequada para triagem.`);

// --------------------------------------------------------------- 9 teste
const s9 = pres.addSlide({ masterName: "CLARO" });
titulo(s9, "A diferença é real, mas pequena", "Teste t 5×2cv de Dietterich com correção de Holm (α = 0,05)");
const pares = [["logistica", "random_forest", "LR × RF"], ["logistica", "gradient_boosting", "LR × GB"], ["random_forest", "gradient_boosting", "RF × GB"]];
const tab = [["Par", "Δ AUC", "p (Holm)", "Δ erro", "p (Holm)"]].concat(pares.map(([a, b, rot]) => {
  const p = par(a, b);
  return [rot, num(p.auc_roc.dif_media), num(p.auc_roc.p_holm), num(p.erro.dif_media), num(p.erro.p_holm)];
}));
s9.addTable(tab.map((l, i) => l.map((c, j) => ({
  text: c,
  options: {
    bold: i === 0 || (j === 2 && i > 0 && Number(c.replace(",", ".")) < 0.05),
    color: i === 0 ? BRANCO : (j === 2 && i > 0 && Number(c.replace(",", ".")) < 0.05 ? LARANJA : TINTA),
    fill: { color: i === 0 ? NAVY : (i % 2 ? TINTE : BRANCO) },
  },
}))), {
  x: MARGEM + 0.8, y: 1.8, w: UTIL - 1.6, colW: [2.6, 2.0, 2.0, 2.0, 1.7],
  fontFace: CORPO_FONTE, fontSize: 17, align: "center", valign: "middle", rowH: 0.55,
  border: { type: "none" },
});
cartao(s9, {
  x: MARGEM, y: 4.25, w: 5.85, h: 1.7, marca: "✓", cor: VERDE, titulo: "Ensembles > Logística",
  texto: "Em AUC, os dois superam o baseline; entre si, sem diferença significativa.",
});
cartao(s9, {
  x: MARGEM + 6.05, y: 4.25, w: 5.85, h: 1.7, marca: "≈", cor: LARANJA, titulo: "Mas só ~0,01 de AUC",
  texto: "No limiar 0,5, nenhum par difere na taxa de erro.",
});
faixa(s9, "Três algoritmos no mesmo patamar: o limite parece estar na informação, não no algoritmo.", { y: 6.15, h: 0.75 });
notas(s9, P3, "Média de métricas não basta para declarar superioridade. Para um único dataset, os slides recomendam o 5×2cv de Dietterich, que controla melhor o erro Tipo I. Cada execução repete a busca interna. Holm corrige as três comparações.");

// -------------------------------------------------------------- 10 limiar
const s10 = pres.addSlide({ masterName: "CLARO" });
titulo(s10, "O limiar decide se o modelo serve para triagem", "Curvas dos três modelos; números à direita: Gradient Boosting");
figura(s10, "fig3_curvas.png", { x: MARGEM, y: 1.6, wMax: 7.0, hMax: 4.2 });
const mt = INT.matriz_triagem;
estatistica(s10, {
  x: MARGEM + 7.4, y: 1.65, w: 4.5, cor: AZUL, valor: `${num(media("gradient_boosting", "sensibilidade"), 2)} → ${num(media("gradient_boosting", "sensibilidade", "triagem"), 2)}`,
  rotulo: "sensibilidade: limiar 0,5 → limiar de triagem",
});
estatistica(s10, {
  x: MARGEM + 7.4, y: 3.15, w: 4.5, cor: LARANJA, valor: `${num(media("gradient_boosting", "especificidade"), 2)} → ${num(media("gradient_boosting", "especificidade", "triagem"), 2)}`,
  rotulo: "especificidade: o preço da sensibilidade",
});
faixa(s10, `Dispensaria ${pct(mt.tn / (mt.tn + mt.fp) * 100, 0)} das crianças normais e deixaria passar ${pct(mt.fn / (mt.fn + mt.tp) * 100, 0)} das cardiopatias: prioriza a fila, não substitui o especialista.`, { y: 6.05, h: 0.9 });
notas(s10, P3, `No limiar 0,5 o modelo perderia mais de um terço das cardiopatias. O limiar de triagem ficou entre ${num(Math.min(...NI.gradient_boosting.folds.map((f) => f.limiar_triagem)), 2)} e ${num(Math.max(...NI.gradient_boosting.folds.map((f) => f.limiar_triagem)), 2)}, escolhido no treino.`);

// ---------------------------------------------------------------- 11 erros
const s11 = pres.addSlide({ masterName: "CLARO" });
titulo(s11, "Onde o modelo erra", "Taxa de falsos negativos entre os anormais (limiar 0,5 → triagem)");
const motivos = [
  ["5 - Parecer cardiológico", "Parecer cardiológico"], ["2 - Check-up", "Check-up"],
  ["6 - Suspeita de cardiopatia", "Suspeita de cardiopatia"], ["1 - Cardiopatia já estabelecida", "Cardiopatia estabelecida"],
];
motivos.forEach(([chave, rot], i) => {
  const a = fn("perfil_fn_05", "motivo1", chave);
  const b = fn("perfil_fn_triagem", "motivo1", chave);
  estatistica(s11, {
    x: MARGEM + i * 3.0, y: 1.75, w: 2.85, tamanho: 30, cor: i < 2 ? LARANJA : AZUL,
    valor: `${pct(a, 0)} → ${pct(b, 0)}`, rotulo: rot,
  });
});
cartao(s11, {
  x: MARGEM, y: 3.6, w: 5.85, h: 2.3, marca: "↑", cor: LARANJA, titulo: "Mais erro nas crianças maiores",
  texto: `O erro cresce com a idade: ${pct(fn("perfil_fn_05", "faixa_etaria", "Lactente"), 0)} dos lactentes anormais escapam, contra ${pct(fn("perfil_fn_05", "faixa_etaria", "Adolescente"), 0)} dos adolescentes.`,
});
cartao(s11, {
  x: MARGEM + 6.05, y: 3.6, w: 5.85, h: 2.3, marca: "♥", cor: NAVY, titulo: "A ausculta segue indispensável",
  texto: `${pct(INT.perfil_fn_05.pct_fn_com_sopro, 0)} dos falsos negativos tinham sopro. Mas o modelo perde mais as cardiopatias sem sopro: ${pct(fn("perfil_fn_05", "sopro", "sem sopro"), 0)} contra ${pct(fn("perfil_fn_05", "sopro", "com sopro"), 0)}.`,
});
notas(s11, P3, "Os erros não são aleatórios: o modelo acerta quando quem encaminhou já suspeitava e erra nos encaminhamentos de rotina (parecer pré-operatório e check-up).");

// ----------------------------------------------------------- 12 importância
const s12 = pres.addSlide({ masterName: "CLARO" });
titulo(s12, "O que o modelo aprendeu", "Importância por permutação (queda da AUC-ROC) e razões de chance da logística");
figura(s12, "fig4_erros.png", { x: MARGEM, y: 1.45, wMax: 5.6, hMax: 4.6 });
const imp = INT.importancia.gradient_boosting;
const top = Object.keys(imp).slice(0, 4);
s12.addText(top.map((k, i) => ({
  text: `${i + 1}. ${k}: −${num(imp[k].media)} de AUC`, options: { breakLine: true, bold: i === 0 },
})), {
  x: MARGEM + 6.1, y: 1.6, w: 5.8, h: 1.9, isTextBox: true, margin: 0,
  fontFace: CORPO_FONTE, fontSize: 18, color: TINTA, valign: "top",
});
const or = INT.logistica.coeficientes;
estatistica(s12, {
  x: MARGEM + 6.1, y: 3.65, w: 5.8, cor: LARANJA, tamanho: 38,
  valor: `e^β = ${num(or["cat__MOTIVO2_6 - Sopro"].razao_de_chance, 2)}`,
  rotulo: "maior efeito positivo da logística: encaminhamento por sopro (efeito relativo, modelo regularizado)",
});
faixa(s12, "O modelo aprende a suspeita de quem encaminhou, refinada por FC e sintomas.", { y: 6.15, h: 0.75 });
notas(s12, P3, `Com one-hot completo e regularização, e^β é efeito relativo, sem categoria de referência. Cardiopatia já estabelecida: ${num(or["cat__MOTIVO1_1 - Cardiopatia já estabelecida"].razao_de_chance, 2)}; check-up puxa para baixo (${num(or["cat__MOTIVO1_2 - Check-up"].razao_de_chance, 2)}). Medidas antropométricas correlacionadas dividem a importância.`);

// -------------------------------------------------------------- 13 conclusão
const s13 = pres.addSlide({ masterName: "ESCURO" });
s13.addText("Conclusão", {
  x: MARGEM, y: 0.55, w: UTIL, h: 0.7, isTextBox: true, margin: 0,
  fontFace: TITULO_FONTE, fontSize: 32, bold: true, color: BRANCO,
});
const blocos = [
  ["Resultado", `Sem vazamento, AUC-ROC ${num(media("gradient_boosting", "auc_roc"))} (RF sem diferença significativa). Com ${pct(mt.tp / (mt.tp + mt.fn) * 100, 0)} de sensibilidade, especificidade de ${num(media("gradient_boosting", "especificidade", "triagem"), 2)}: prioriza a fila, não dispensa a ausculta.`],
  ["Limitações", `Um hospital, quase tudo de 2003–2010, prevalência em queda; chave de paciente aproximada; sem os casos de cardiopatia já estabelecida, a AUC agregada cai para ${num(INT.sem_cardiopatia_estabelecida.auc_roc)}.`],
  ["Próximos passos", "Validação temporal, calibração, limiar pelos custos clínicos e fonocardiograma digital na triagem."],
];
blocos.forEach(([t, texto], i) => {
  s13.addText(t, {
    x: MARGEM, y: 1.55 + i * 1.45, w: 3.0, h: 1.2, isTextBox: true, margin: 0, valign: "top",
    fontFace: TITULO_FONTE, fontSize: 19, bold: true, color: LARANJA,
  });
  s13.addText(texto, {
    x: MARGEM + 3.1, y: 1.55 + i * 1.45, w: UTIL - 3.1, h: 1.2, isTextBox: true, margin: 0, valign: "top",
    fontFace: CORPO_FONTE, fontSize: 18, color: "E6ECF7",
  });
});
s13.addText("Obrigado. Perguntas?", {
  x: MARGEM, y: 6.05, w: UTIL, h: 0.6, isTextBox: true, margin: 0,
  fontFace: TITULO_FONTE, fontSize: 24, bold: true, color: BRANCO,
});
notas(s13, P3, "Código e resultados no repositório citado no rodapé do artigo, com random_state = 42.");

const destino = path.join(RAIZ, "slides", "Apresentacao_A2.pptx");
fs.mkdirSync(path.dirname(destino), { recursive: true });
pres.writeFile({ fileName: destino }).then(() => console.log(`Gravado: ${destino}`));
