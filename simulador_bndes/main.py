from simulador_bndes import simulador_bndes
from tabulate import tabulate

def main():
    # Inicializa o simulador com os parâmetros do financiamento
    simulador = simulador_bndes(
        data_contratacao="09/10/2024",      # Data de contratação do financiamento
        valor_liberado=200000.00,           # Valor liberado (em reais)
        carencia=3,                         # Período de carência em meses
        periodic_juros=1,                   # Periodicidade do pagamento de juros (meses)
        prazo_amortizacao=10,               # Prazo de amortização (meses)
        periodic_amortizacao=3,             # Periodicidade de pagamento de amortização (meses)
        juros_prefixados_aa=6.31,           # Taxa de juros prefixados anual (% a.a.)
        ipca_mensal=0.44,                   # IPCA mensal (opcional)
        spread_bndes_aa=1.15,               # Spread BNDES anual (opcional)
        spread_banco_aa=5.75                # Spread banco anual (opcional)
    )

    # Gera os resultados do pagamento
    resultados = simulador.exibir_dados_pagamento(exportar_csv=False)

    # Exibe os resultados em formato tabular no terminal
    print(tabulate(resultados, headers="keys", tablefmt="grid"))

if __name__ == "__main__":
    main()
