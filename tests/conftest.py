"""Configuração comum dos testes: põe `src/` no caminho e roda da raiz da A2."""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
os.chdir(RAIZ)
