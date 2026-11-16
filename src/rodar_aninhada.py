"""Roda a validação aninhada completa dos quatro modelos (execução longa)."""

import base_dados
import config
import experimento

if __name__ == "__main__":
    X, y, grupos, base = base_dados.carregar_base(config.RAW)
    experimento.rodar_todos(X, y, grupos, base)
