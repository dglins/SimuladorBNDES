# simulador.py
from datetime import datetime, timedelta
from .utils import proxima_data_ipca, calcula_proxima_data_util
from .api import obter_tlp, obter_ipca
from .calculos import calcular_amortizacao_principal, calcular_juros_bndes, calcular_juros_banco
import json
import pandas as pd

class SimuladorBNDES:
    def __init__(self, data_contratacao, valor_liberado, carencia, periodic_juros, prazo_amortizacao,
                 periodic_amortizacao, juros_prefixados_aa, ipca_mensal=None, spread_bndes_aa=None, spread_banco_aa=None):
        self.data_contratacao = datetime.strptime(data_contratacao, "%d/%m/%Y")
        self.valor_liberado = valor_liberado
        self.saldo_devedor = valor_liberado
        self.carencia = carencia
        self.periodic_juros = periodic_juros
        self.prazo_amortizacao = prazo_amortizacao
        self.periodic_amortizacao = periodic_amortizacao
        self.juros_prefixados_aa = juros_prefixados_aa

        # Taxas anuais fornecidas ou calculadas
        self.ipca_mensal = ipca_mensal or obter_ipca()
        self.spread_bndes_aa = spread_bndes_aa or obter_tlp()
        self.spread_banco_aa = spread_banco_aa or self._carregar_configuracao("spread_banco_aa")

        # Converte taxas anuais para mensais
        self.juros_prefixados_am = (1 + self.juros_prefixados_aa / 100) ** (1 / 12) - 1
        self.spread_bndes_am = (1 + self.spread_bndes_aa / 100) ** (1 / 12) - 1
        self.spread_banco_am = (1 + self.spread_banco_aa / 100) ** (1 / 12) - 1

    @staticmethod
    def _carregar_configuracao(chave):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            return config.get(chave, 0)
        except FileNotFoundError:
            return 0
    def calcular_amortizacao_principal(self):
        """
        Calcula a amortização principal com base no saldo devedor atual e no número de prestações restantes.
        """
        return calcular_amortizacao_principal(self.saldo_devedor, self.prazo_amortizacao)

    def exibir_dados_pagamento(self, exportar_csv=False):
        """
        Gera e exibe o cronograma de pagamentos do financiamento.
        """
        resultados = []
        mes_atual = 0

        while mes_atual <= self.prazo_amortizacao:
            # Calcula as informações do mês atual
            saldo_devedor = self.saldo_devedor
            amortizacao = calcular_amortizacao_principal(saldo_devedor, self.prazo_amortizacao)
            juros_bndes = calcular_juros_bndes(saldo_devedor, fator_4=1.02)  # Exemplo com fator_4 fixo
            juros_banco = calcular_juros_banco(saldo_devedor, spread_banco_am= self.spread_banco_am)
            parcela_total = round(amortizacao + juros_bndes + juros_banco, 2)

            # Adiciona os resultados do mês
            resultados.append({
                "Mês": mes_atual,
                "Parcela": mes_atual if mes_atual > 0 else "-",
                "Data Vencimento": (self.data_contratacao + timedelta(days=mes_atual * 30)).strftime("%d/%m/%Y"),
                "Amortização Principal": amortizacao,
                "Juros BNDES": juros_bndes,
                "Juros Banco": juros_banco,
                "Parcela Total": parcela_total,
                "Saldo Devedor": saldo_devedor
            })

            # Atualiza o saldo devedor e avança para o próximo mês
            self.saldo_devedor -= amortizacao
            mes_atual += 1

        # Exporta para CSV se solicitado
        if exportar_csv:
            df = pd.DataFrame(resultados)
            df.to_csv("simulador_resultados.csv", index=False)
            print("Resultados exportados para 'simulador_resultados.csv'.")

        return resultados