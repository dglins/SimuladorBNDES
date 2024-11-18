import streamlit as st
from Simulador import SimuladorBNDES

# Cria o app usando Streamlit
st.title("Simulador de Pagamentos BNDES")

# Regras de prazo máximo e carência
regras = {
    "BK Aquisição e Comercialização (FINAME)": {"prazo_max": 120, "carencia_max": 24},
    "BNDES Automático - Projeto de Investimento": {"prazo_max": 240, "carencia_max": 36},
    "BNDES Finame - Baixo Carbono": {"prazo_max": 120, "carencia_max": 24}  # Exemplo
}

# Seleção do produto
produto = st.selectbox(
    "Produto",
    ["BK Aquisição e Comercialização (FINAME)", "BNDES Automático - Projeto de Investimento", "BNDES Finame - Baixo Carbono"]
)

# Obtém os valores máximos com base no produto selecionado
prazo_max = regras[produto]["prazo_max"]
carencia_max = regras[produto]["carencia_max"]
carencia_minima = 3

st.write(f"**Regras do Produto Selecionado:**\n"
         f"- Prazo + Carência Máximo: {prazo_max} meses\n"
         f"- Carência Mínima: {carencia_minima} meses\n"
         f"- Prazo Máximo: {prazo_max - carencia_minima} meses\n"
         f"- Carência Máxima: {carencia_max} meses")

# Entradas do usuário
st.write("### Configurações do Simulador")

# Inputs na mesma linha para períodos
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    carencia = st.number_input(
        "Carência (meses)",
        min_value=3,
        max_value=carencia_max,
        value=3,
        help="Informe o período de carência, ou seja, o tempo inicial antes do início dos pagamentos (mín. 3 meses)."
    )
with col2:
    prazo_amortizacao = st.number_input(
        "Amortização (meses)",
        min_value=1,
        value=24,
        help="Informe o prazo para amortização (tempo para quitação do saldo devedor)."
    )
with col3:
    periodic_juros = st.number_input(
        "Per. Juros (meses)",
        min_value=1,
        value=1,
        help="Informe a periodicidade do pagamento dos juros em meses."
    )
with col4:
    periodic_amortizacao = st.number_input(
        "Per. Amortização (meses)",
        min_value=1,
        value=1,
        help="Informe a periodicidade do pagamento de amortização em meses."
    )

# Inputs na mesma linha para taxas e spreads
col5, col6, col7, col8 = st.columns([1, 1, 1, 1])
with col5:
    juros_prefixados_aa = st.number_input(
        "Juros Prefixados (% a.a.)",
        min_value=0.0,
        value=6.43,
        help="Taxa de juros anual prefixada para o financiamento."
    )
with col6:
    ipca_mensal = st.number_input(
        "IPCA (% a.m.)",
        min_value=0.0,
        value=0.56,
        help="Informe a variação do IPCA mensal, usado para calcular a correção monetária."
    )
with col7:
    spread_bndes_aa = st.number_input(
        "Spread BNDES (% a.a.)",
        min_value=0.0,
        value=0.95,
        help="Informe o spread anual aplicado pelo BNDES ao financiamento."
    )
with col8:
    spread_banco_aa = st.number_input(
        "Spread Banco (% a.a.)",
        min_value=0.0,
        value=5.75,
        help="Informe o spread anual aplicado pelo banco intermediário ao financiamento."
    )

# Botão para realizar a simulação
if st.button("Simular"):
    prazo_total = carencia + prazo_amortizacao

    if prazo_total > prazo_max:
        st.error(
            f"O prazo total (Carência + Amortização) para o produto selecionado "
            f"({produto}) é de no máximo {prazo_max} meses. Você informou {prazo_total} meses.\n\n"
            f"Por favor, ajuste o período de carência ou o prazo de amortização para que o prazo total "
            f"não ultrapasse o limite permitido."
        )
    else:
        # Inicializa o simulador com os parâmetros fornecidos
        simulador = SimuladorBNDES(
            data_contratacao="15/10/2024",  # Aqui você pode ajustar o valor fixo ou parametrizado
            valor_liberado=200_000.0,  # Ajustar conforme necessidade
            carencia=carencia,
            periodic_juros=periodic_juros,
            prazo_amortizacao=prazo_amortizacao,
            periodic_amortizacao=periodic_amortizacao,
            juros_prefixados_aa=juros_prefixados_aa,
            ipca_mensal=ipca_mensal,
            spread_bndes_aa=spread_bndes_aa,
            spread_banco_aa=spread_banco_aa
        )

        # Gera os resultados da simulação
        resultados_df = simulador.exibir_dados_pagamento()

        # Exibe os resultados em uma tabela
        st.write("### Resultados da Simulação")
        st.dataframe(resultados_df, use_container_width=True)
