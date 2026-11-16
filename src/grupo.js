/**
 * Número do grupo e integrantes, lidos de grupo.json na raiz do projeto.
 *
 * Relatório, slides e guia usam a mesma linha, para que os nomes sejam
 * preenchidos num lugar só. Sem nomes, a linha sai com os traços de
 * preenchimento; sem o número, sai só a lista de integrantes.
 */

const fs = require("fs");
const path = require("path");

const dados = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "grupo.json"), "utf8"));
const nomes = (dados.integrantes || []).map((n) => String(n).trim()).filter(Boolean);
const numero = String(dados.grupo || "").trim();

/** "A, B e C", como se escreve uma lista em português. */
const juntar = (lista) => (lista.length <= 1
  ? lista.join("")
  : `${lista.slice(0, -1).join(", ")} e ${lista[lista.length - 1]}`);

const linha = (separador = " · ") => {
  if (!nomes.length) {
    return `Grupo ${numero || "__"}${separador}Integrantes: ______________________________________________`;
  }
  const integrantes = `Integrantes: ${juntar(nomes)}`;
  return numero ? `Grupo ${numero}${separador}${integrantes}` : integrantes;
};

module.exports = { preenchido: nomes.length > 0, linha, nomes, numero, juntar };
