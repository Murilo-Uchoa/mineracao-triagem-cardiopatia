"""Monta o pacote da A2 para compartilhar com o grupo.

    python src/empacotar.py   ->  pacote/A2_UCMF.zip

O .zip abre numa pasta A2_UCMF/ com o guia na raiz, o artigo e a
apresentação em pastas próprias e o projeto completo, que roda do zero com
`python executar.py`. É material interno do grupo (contém os dados), não o
repositório público. Ficam de fora caches, node_modules e o próprio pacote.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "pacote" / "A2_UCMF.zip"
PASTA = "A2_UCMF"

ATALHOS = {
    "LEIA PRIMEIRO - Guia da A2.pdf": "guia/Guia_A2.pdf",
    "1 - Artigo (entregar no SIGAA)/Artigo_A2_UCMF.pdf": "relatorio/main.pdf",
    "2 - Apresentação/Apresentacao_A2.pptx": "slides/Apresentacao_A2.pptx",
    "2 - Apresentação/Apresentacao_A2.pdf": "slides/Apresentacao_A2.pdf",
}
PROJETO = "3 - Projeto completo (código e dados)"

IGNORAR_PASTAS = {"__pycache__", ".pytest_cache", "node_modules", "pacote", ".git"}


def arquivos_do_projeto():
    for caminho in sorted(RAIZ.rglob("*")):
        relativo = caminho.relative_to(RAIZ)
        if caminho.is_dir() or IGNORAR_PASTAS & set(relativo.parts):
            continue
        if caminho.name.startswith("~$"):
            continue
        yield relativo


def main():
    faltando = [origem for origem in ATALHOS.values() if not (RAIZ / origem).exists()]
    if faltando:
        print("faltam arquivos gerados:", ", ".join(faltando))
        return 1
    DESTINO.parent.mkdir(exist_ok=True)
    total = 0
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as pacote:
        for nome, origem in ATALHOS.items():
            pacote.write(RAIZ / origem, f"{PASTA}/{nome}")
        for relativo in arquivos_do_projeto():
            pacote.write(RAIZ / relativo, f"{PASTA}/{PROJETO}/{relativo.as_posix()}")
            total += 1
    print(f"escrito: {DESTINO}")
    print(f"{len(ATALHOS)} atalhos + {total} arquivos do projeto, "
          f"{DESTINO.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
