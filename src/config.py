"""Constantes do experimento da A2 (estudo de caso UCMF).

Tudo o que precisa ser igual em todos os módulos — semente, caminhos, alvo e a
lista de atributos — fica aqui, num só lugar.
"""

from __future__ import annotations

from pathlib import Path

SEED = 42

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "dados"
RAW = DADOS / "UCMF_raw.csv"
TABELA_PA = DADOS / "referencia" / "tabela_pa.csv"
RESULTADOS = RAIZ / "resultados"
FIGURAS = RAIZ / "figuras"
RELATORIO = RAIZ / "relatorio"

ALVO = "NORMAL X ANORMAL"
POSITIVO = "Anormal"
NAO_INFORMADO = "Não informado"

# Atributos do modelo (13). A ordem é a das colunas de X.
NUMERICAS = ["Peso", "Altura", "IMC", "IDADE", "FC"]
BINARIAS = ["PA_medida"]
CATEGORICAS = ["PPA", "PULSOS", "HDA 1", "SEXO", "MOTIVO1", "MOTIVO2"]
CONVENIO = "Convenio"
ATRIBUTOS = NUMERICAS + BINARIAS + CATEGORICAS + [CONVENIO]

# Achados da ausculta cardíaca, o exame que produz o próprio diagnóstico.
VAZAMENTO = ["SOPRO", "B2"]

# Validação (design, seção 9.5) e limiar de triagem (seção 9.7).
N_EXTERNO = 10
N_INTERNO = 5
SENSIBILIDADE_TRIAGEM = 0.90
SEEDS_5X2 = (42, 43, 44, 45, 46)
