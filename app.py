import streamlit as st
from Simulador import SimuladorBNDES


# Cria o app usando Streamlit
st.title("Simulador de Pagamentos BNDES")

# Entradas do usuário para os parâmetros do simulador
data_contratacao = st.text_input("Data de Contratação (dd/mm/yyyy)", "15/10/2024")
valor_liberado = st.number_input("Valor Liberado (em R$)", min_value=0.0, value=200000.0)
carencia = st.number_input("Período de Carência (meses)", min_value=0, value=3)
periodic_juros = st.number_input("Periodicidade do Pagamento de Juros (meses)", min_value=1, value=1)
prazo_amortizacao = st.number_input("Prazo de Amortização (meses)", min_value=1, value=20)
periodic_amortizacao = st.number_input("Periodicidade do Pagamento de Amortização (meses)", min_value=1, value=3)
juros_prefixados_aa = st.number_input("Taxa de Juros Prefixados Anual (% a.a.)", min_value=0.0, value=6.31)
ipca_mensal = st.number_input("Variação Mensal do IPCA (% a.m.)", min_value=0.0, value=0.44)
spread_bndes_aa = st.number_input("Spread do BNDES Anual (% a.a.)", min_value=0.0, value=1.15)
spread_banpara_aa = st.number_input("Spread do BANCO Anual (% a.a.)", min_value=0.0, value=5.75)

# Botão para realizar a simulação
if st.button("Simular"):
    # Inicializa o simulador com os parâmetros fornecidos
    simulador = SimuladorBNDES(
        data_contratacao=data_contratacao,
        valor_liberado=valor_liberado,
        carencia=carencia,
        periodic_juros=periodic_juros,
        prazo_amortizacao=prazo_amortizacao,
        periodic_amortizacao=periodic_amortizacao,
        juros_prefixados_aa=juros_prefixados_aa,
        ipca_mensal=ipca_mensal,
        spread_bndes_aa=spread_bndes_aa,
        spread_banco_aa=spread_banpara_aa
    )

    # Gera os resultados da simulação
    resultados_df = simulador.exibir_dados_pagamento()

    # Exibe os resultados em uma tabela
    st.write("### Resultados da Simulação")
    st.dataframe(resultados_df)

    # Opção para exportar os resultados para CSV
    if st.button("Exportar para CSV"):
        resultados_df.to_csv("simulador_sudes_resultados.csv", index=False)
        st.success("Resultados exportados para 'simulador_sudes_resultados.csv'")
