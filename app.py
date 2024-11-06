import streamlit as st
from pandas import to_datetime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from lista_feriados import feriados
import pandas as pd


# Incluindo sua classe SimuladorSudes
class SimuladorSudes:
    def __init__(self, data_contratacao: str, valor_liberado: float, carencia: int,
                 periodic_juros: int, prazo_amortizacao: int,
                 periodic_amortizacao: int, juros_prefixados_aa: float,
                 ipca_mensal: float, spread_bndes_aa: float, spread_banpara_aa: float):
        # Inicializa os parâmetros
        self.data_contratacao = datetime.strptime(data_contratacao, "%d/%m/%Y")
        self.valor_liberado = valor_liberado
        self.saldo_devedor = valor_liberado
        self.carencia = carencia
        self.periodic_juros = periodic_juros
        self.prazo_amortizacao = prazo_amortizacao
        self.periodic_amortizacao = periodic_amortizacao
        self.juros_prefixados_aa = juros_prefixados_aa
        self.ipca_mensal = ipca_mensal
        self.spread_bndes_aa = spread_bndes_aa
        self.spread_banpara_aa = spread_banpara_aa
        self.feriados = [to_datetime(f, dayfirst=True).date() for f in feriados]
        self.quantidade_prestacoes = prazo_amortizacao // periodic_amortizacao
        self.quantidade_prestacoes_restantes = prazo_amortizacao // periodic_amortizacao

        # Calcula a quantidade de prestações e converte taxas anuais para mensais
        self.juros_prefixados_am = (1 + juros_prefixados_aa / 100) ** (1 / 12) - 1
        self.spread_bndes_am = (1 + spread_bndes_aa / 100) ** (1 / 12) - 1
        self.spread_banpara_am = (1 + spread_banpara_aa / 100) ** (1 / 12) - 1
        self.taxa_total_mensal = (self.juros_prefixados_am +
                                  self.spread_bndes_am +
                                  self.spread_banpara_am +
                                  self.ipca_mensal / 100)

    def exibir_dados_pagamento(self):
        """
        Exibe os dados de pagamento em formato tabular.
        """
        mes_atual = 0
        fator_4_anterior = None
        data_pagamento_anterior = None
        resultados = []

        while True:
            # Verifica os dados de pagamento (juros e/ou amortização)
            pagamento_info = self.verificar_data_pagamento(mes_atual)

            # Define data de vencimento e contador de parcelas
            data_vencimento = None
            contador = None
            if pagamento_info:
                data_vencimento = self.data_contratacao + relativedelta(months=mes_atual)
                contador = pagamento_info["numero_parcela"] if pagamento_info["pagar_amortizacao"] else None

            # Calcula amortização principal e atualiza saldo devedor
            amortizacao_principal = None
            if pagamento_info and pagamento_info["pagar_amortizacao"]:
                amortizacao_principal = self.calcula_amortizacao_principal()

            # Calcula juros BNDES e BANPARA
            juros_bndes = self.calcular_juros_bndes() if pagamento_info else 0
            juros_banpara = self.calcular_juros_banpara() if pagamento_info else 0

            # Calcula o valor total da parcela
            valor_parcela = (amortizacao_principal or 0) + juros_bndes + juros_banpara if pagamento_info else "N/A"

            # Armazena os resultados
            resultados.append({
                "Mês": mes_atual,
                "Parcela": contador if contador else "N/A",
                "Data Vencimento": data_vencimento.strftime('%d/%m/%Y') if data_vencimento else "N/A",
                "Amortização Principal": round(amortizacao_principal, 2) if amortizacao_principal else "N/A",
                "Juros BNDES": juros_bndes,
                "Juros BANPARA": juros_banpara,
                "Parcela Total": round(valor_parcela, 2) if isinstance(valor_parcela, float) else "N/A",
                "Saldo Devedor": round(self.saldo_devedor, 2)
            })

            # Interrompe o loop ao atingir o número máximo de parcelas
            if pagamento_info and pagamento_info["pagar_amortizacao"]:
                self.atualizar_saldo_devedor(amortizacao_principal)
            if pagamento_info and pagamento_info["pagar_amortizacao"] and contador == self.quantidade_prestacoes:
                break

            mes_atual += 1

        # Retorna os resultados em formato DataFrame para exibição
        return pd.DataFrame(resultados)

    def verificar_data_pagamento(self, mes_atual):
        pagamento_info = {
            "pagar_juros": False,
            "pagar_amortizacao": False,
            "numero_parcela": None
        }

        if mes_atual == 0:
            return None

        if mes_atual <= self.carencia:
            if mes_atual % self.periodic_juros == 0:
                pagamento_info["pagar_juros"] = True
        else:
            if (mes_atual - self.carencia) % self.periodic_amortizacao == 0:
                pagamento_info["pagar_amortizacao"] = True
                pagamento_info["pagar_juros"] = True
                pagamento_info["numero_parcela"] = (mes_atual - self.carencia) // self.periodic_amortizacao

        if not pagamento_info["pagar_juros"] and not pagamento_info["pagar_amortizacao"]:
            return None

        return pagamento_info

    def calcula_amortizacao_principal(self):
        amortizacao_principal = self.saldo_devedor / self.quantidade_prestacoes_restantes
        return amortizacao_principal

    def atualizar_saldo_devedor(self, amortizacao_principal):
        self.saldo_devedor -= amortizacao_principal
        self.quantidade_prestacoes_restantes -= 1

    def calcular_juros_bndes(self):
        juros_bndes = round(self.saldo_devedor * (self.juros_prefixados_am), 2)
        return juros_bndes

    def calcular_juros_banpara(self):
        juros_banpara = round(self.saldo_devedor * (self.spread_banpara_am), 2)
        return juros_banpara


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
    simulador = SimuladorSudes(
        data_contratacao=data_contratacao,
        valor_liberado=valor_liberado,
        carencia=carencia,
        periodic_juros=periodic_juros,
        prazo_amortizacao=prazo_amortizacao,
        periodic_amortizacao=periodic_amortizacao,
        juros_prefixados_aa=juros_prefixados_aa,
        ipca_mensal=ipca_mensal,
        spread_bndes_aa=spread_bndes_aa,
        spread_banpara_aa=spread_banpara_aa
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
