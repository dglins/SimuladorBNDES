# calculos.py
def calcular_amortizacao_principal(saldo_devedor, quantidade_prestacoes):
    """
    Calcula a amortização principal.
    """
    return saldo_devedor / quantidade_prestacoes

def calcular_juros_bndes(saldo_devedor, fator_4):
    """
    Calcula os juros do BNDES.
    """
    return round(saldo_devedor * (fator_4 - 1), 2)

def calcular_juros_banco(saldo_devedor, spread_banco_am):
    """
    Calcula os juros do banco.
    """
    fator_banco = (1 + spread_banco_am)
    return round(saldo_devedor * (fator_banco - 1), 2)
