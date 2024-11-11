from simulador_bndes import SimuladorBNDES

if __name__ == "__main__":
    simulador = SimuladorBNDES(
        data_contratacao="09/10/2024",
        valor_liberado=200000.00,
        carencia=12,
        periodic_juros=2,
        prazo_amortizacao=60,
        periodic_amortizacao=1,
        juros_prefixados_aa=6.31,
        spread_banco_aa=5.75,              # Spread do banco anual (% a.a.)
        ipca_mensal = 0.44,
        spread_bndes_aa = 1.15
    )
    resultados = simulador.exibir_dados_pagamento()
    for resultado in resultados:
        print(resultado)
