import config


def test_atributos_sem_vazamento():
    assert len(config.ATRIBUTOS) == 13
    proibidos = config.VAZAMENTO + ["ID", "Atendimento", "DN", "FAIXA_ETARIA"]
    assert not set(proibidos) & set(config.ATRIBUTOS)
    assert config.VAZAMENTO == ["SOPRO", "B2"]
    assert config.SEED == 42
