import verificar_relatorio as vr

NUMEROS = "\\defnum{n}{11{.}454}\n\\defnum{auc}{0{,}787}\n"


def test_codigo_no_tex_e_apontado(tmp_path):
    tex = "\\begin{lstlisting}\nprint(1)\n\\end{lstlisting}"
    problemas = vr.verificar_tex(tex, NUMEROS)
    assert any("código" in p for p in problemas)


def test_dado_indefinido_e_apontado():
    problemas = vr.verificar_tex("Temos \\dado{n} e \\dado{inexistente}.", NUMEROS)
    assert any("inexistente" in p for p in problemas)
    assert not any("'n'" in p for p in problemas)


def test_label_sem_ref_e_apontado():
    tex = "\\begin{figure}\\label{fig:a}\\end{figure} Ver Fig.~\\ref{fig:b}."
    problemas = vr.verificar_tex(tex, NUMEROS)
    assert any("fig:a" in p for p in problemas)


def test_contagem_do_resumo():
    tex = ("\\begin{abstract}Este resumo tem \\dado{n} casos e AUC de \\dado{auc}, "
           "com o \\emph{melhor} modelo.\\end{abstract}")
    # Este resumo tem 11.454 casos e AUC de 0,787, com o melhor modelo. → 13
    assert vr.palavras_do_resumo(tex, NUMEROS) == 13


def test_resumo_fora_da_faixa_e_apontado():
    tex = "\\begin{abstract}Curto demais.\\end{abstract}"
    assert any("resumo" in p for p in vr.verificar_tex(tex, NUMEROS))
