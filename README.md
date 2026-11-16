# Triagem de cardiopatia pediátrica sem vazamento de dados — estudo de caso UCMF

Trabalho da disciplina **Mineração de Dados / KDD** (Instituto de Informática, UFG,
Prof. Rogerio Salvini, 2026), avaliação A2. Integrantes: Murilo Uchôa, Felipe Orlow
e João Henrique Simielli.

**Pergunta:** é possível estimar o risco de cardiopatia em crianças *antes* da
ausculta do cardiologista, usando só dados do encaminhamento, antropometria, sinais
vitais e sintomas? Classificação binária (`Normal` × `Anormal`), comparando
regressão logística (baseline), *random forest* e *gradient boosting*.

## Resultado principal

| Modelo | AUC-ROC (média ± dp, 10 partições) |
|---|---|
| Classe majoritária (piso) | 0,500 |
| Regressão Logística | 0,770 ± 0,014 |
| Random Forest | 0,785 ± 0,015 |
| Gradient Boosting | 0,787 ± 0,014 |

Pelo teste 5×2cv de Dietterich com correção de Holm, os dois *ensembles* superam a
logística na AUC e não diferem entre si. No limiar de triagem (sensibilidade ≥ 0,90,
escolhido no treino), o *gradient boosting* tem especificidade de 0,40. Esses dados
servem para priorizar a fila do especialista, mas não substituem a ausculta.

Os números acima vêm de `resultados/`. O artigo cita os mesmos valores por macros
geradas automaticamente (`relatorio/numeros.tex`).

## Como o vazamento de dados foi evitado

1. **De atributo:** `SOPRO` e `B2` são achados da ausculta, o exame que produz o
   diagnóstico, e ficaram fora do modelo. A regra "tem sopro ⇒ anormal" sozinha
   acerta 92,1%.
2. **De instância:** o ID identifica o atendimento, não a criança, e a base tem
   retornos. A validação usa `StratifiedGroupKFold`, com a chave de paciente
   `data de nascimento + sexo`.
3. **De pré-processamento:** medianas, médias, desvios e frequências são aprendidos
   dentro de um `Pipeline`, somente no treino de cada partição.

## Como reproduzir

Requer Python 3.13. As versões usadas estão fixadas em `requirements.txt`.

```bash
pip install -r requirements.txt
python executar.py
```

`executar.py` vai do CSV bruto às figuras e tabelas do artigo, em cerca de 25 min
numa máquina de 16 núcleos. Ao final, roda 7 verificações automáticas, entre elas
a de que nenhum paciente aparece em treino e teste. Para refazer só as figuras e
tabelas a partir dos resultados salvos:

```bash
python executar.py --etapa artefatos
```

Testes e conferência do artigo (páginas, resumo, link, números):

```bash
python -m pytest
python src/verificar_relatorio.py
```

Todo `random_state` é **42**. O 5×2cv usa as sementes 42 a 46.

### Dados

O conjunto UCMF **não é distribuído neste repositório**. Os dados são de pacientes
do Real Hospital Português (Recife), anonimizados e liberados apenas para estudos
acadêmicos, e foram fornecidos pelo professor aos alunos da disciplina. Para
reproduzir, coloque o arquivo em `dados/UCMF_raw.csv`. A tabela de pressão arterial
pediátrica usada na reconstrução da variável PPA (NHBPEP, 2004, de domínio público)
está em `dados/referencia/tabela_pa.csv`.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `executar.py` | roda tudo e verifica |
| `src/limpeza.py`, `src/referencia_clinica.py` | limpeza herdada da A1, sem a imputação |
| `src/base_dados.py` | atributos do modelo, alvo e chave de paciente |
| `src/transformadores.py` | imputação estratificada, codificação por frequência, pré-processador |
| `src/modelos.py` | algoritmos e grades de hiperparâmetros |
| `src/experimento.py` | validação cruzada aninhada agrupada, limiar de triagem, importância |
| `src/comparacao.py` | teste 5×2cv e correção de Holm |
| `src/auditoria.py` | análise exploratória e auditoria de vazamento |
| `src/interpretacao.py` | matrizes de confusão, perfil dos erros, razões de chance |
| `src/graficos.py`, `src/artefatos.py` | figuras e tabelas/macros do artigo |
| `src/verificar_relatorio.py` | checa o artigo contra o enunciado |
| `src/slides.js` | gera a apresentação (`npm install` e `node src/slides.js`) |
| `tests/` | testes (pytest) |
| `resultados/` | métricas, testes e EDA em JSON (só agregados) |
| `figuras/` | figuras do artigo (PDF e PNG) |
| `relatorio/` | artigo em LaTeX (IEEEtran) e PDF |

O artigo compila com `tectonic relatorio/main.tex` ou no Overleaf.

## Uso de IA generativa

Declarado na seção final do artigo, como exige o enunciado da disciplina.
