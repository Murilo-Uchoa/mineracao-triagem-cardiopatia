"""Confere o artigo contra as exigências do enunciado da A2.

    python src/verificar_relatorio.py

Aponta: mais de 5 páginas; resumo fora de 100–150 palavras; código no
relatório; figura ou tabela rotulada e nunca citada no texto; número
(`\\dado{...}`) sem definição em `numeros.tex`; link do repositório ausente da
primeira página. Sem problemas, sai com código 0.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
URL_REPOSITORIO = "github.com/Murilo-Uchoa/ucmf-triagem-cardiopatia"
PAGINAS_MAX = 5
PALAVRAS_RESUMO = (100, 150)


def _definidos(numeros_tex: str) -> dict[str, str]:
    return dict(re.findall(r"\\defnum\{([^}]+)\}\{(.*)\}$", numeros_tex, flags=re.M))


def palavras_do_resumo(tex: str, numeros_tex: str) -> int | None:
    achado = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, flags=re.S)
    if not achado:
        return None
    valores = _definidos(numeros_tex)
    texto = re.sub(r"\\dado\{([^}]+)\}", lambda m: valores.get(m.group(1), "X").replace(" ", ""),
                   achado.group(1))
    texto = re.sub(r"\\[a-zA-Z]+\*?", " ", texto).replace("~", " ")
    texto = re.sub(r"[{}$]", "", texto)
    return sum(1 for token in texto.split() if re.search(r"\w", token))


def verificar_tex(tex: str, numeros_tex: str) -> list[str]:
    problemas = []
    if re.search(r"\\begin\{(lstlisting|verbatim|minted)\}|\\verb\W", tex):
        problemas.append("há código no relatório (lstlisting/verbatim/minted/\\verb)")

    definidos = _definidos(numeros_tex)
    for chave in sorted(set(re.findall(r"\\dado\{([^}]+)\}", tex)) - set(definidos)):
        problemas.append(f"número indefinido em numeros.tex: '{chave}'")

    citados = set(re.findall(r"\\ref\{([^}]+)\}", tex))
    for rotulo in re.findall(r"\\label\{((?:fig|tab):[^}]+)\}", tex):
        if rotulo not in citados:
            problemas.append(f"rótulo sem referência no texto: {rotulo}")

    n = palavras_do_resumo(tex, numeros_tex)
    if n is None:
        problemas.append("resumo ausente")
    elif not PALAVRAS_RESUMO[0] <= n <= PALAVRAS_RESUMO[1]:
        problemas.append(f"resumo com {n} palavras (exigido: 100 a 150)")
    return problemas


def verificar_pdf(pdf: Path, url: str = URL_REPOSITORIO) -> list[str]:
    import pypdf

    leitor = pypdf.PdfReader(str(pdf))
    problemas = []
    if len(leitor.pages) > PAGINAS_MAX:
        problemas.append(f"{len(leitor.pages)} páginas (máximo: {PAGINAS_MAX})")
    primeira = re.sub(r"\s+", "", leitor.pages[0].extract_text() or "")
    if url.replace(" ", "") not in primeira:
        problemas.append(f"link do repositório ausente da primeira página: {url}")
    return problemas


def verificar(relatorio: Path = RAIZ / "relatorio") -> list[str]:
    tex = (relatorio / "main.tex").read_text(encoding="utf-8")
    numeros = (relatorio / "numeros.tex").read_text(encoding="utf-8")
    problemas = verificar_tex(tex, numeros)
    pdf = relatorio / "main.pdf"
    problemas += verificar_pdf(pdf) if pdf.exists() else ["PDF não compilado"]
    return problemas


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    encontrados = verificar()
    tex = (RAIZ / "relatorio" / "main.tex").read_text(encoding="utf-8")
    numeros = (RAIZ / "relatorio" / "numeros.tex").read_text(encoding="utf-8")
    print(f"Resumo: {palavras_do_resumo(tex, numeros)} palavras")
    for p in encontrados:
        print("PROBLEMA:", p)
    print("OK" if not encontrados else f"{len(encontrados)} problema(s)")
    sys.exit(1 if encontrados else 0)
