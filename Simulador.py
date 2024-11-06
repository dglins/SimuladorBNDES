from pandas import to_datetime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from lista_feriados import feriados
from tabulate import tabulate


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

    def exibir_dados_pagamento(self, exportar_csv=False):
        """
        Exibe os dados de pagamento em formato tabular e opcionalmente exporta para CSV.
        """
        mes_atual = 0
        fator_4_anterior = None
        data_pagamento_anterior = None
        resultados = []

        while True:
            # Determina as datas de aniversário para DUT e DUP
            data_aniversario_anterior = self.proxima_data_ipca(self.data_contratacao + relativedelta(months=mes_atual))
            data_aniversario_subsequente = self.proxima_data_ipca(
                self.data_contratacao + relativedelta(months=mes_atual + 1))

            # Calcula DUT e DUP
            dut = self.calcula_dut(data_aniversario_anterior, data_aniversario_subsequente)
            data_inicio = self.data_contratacao if mes_atual == 0 else data_aniversario_anterior
            data_calculo = self.data_contratacao + relativedelta(months=mes_atual + 1)
            dup = self.calcula_dup(data_inicio, data_calculo, data_aniversario_anterior, data_aniversario_subsequente)

            # Calcula fatores
            fator_1, fator_2, fator_3, fator_4 = self.calcular_fatores(dup, dut, fator_4_anterior,
                                                                       data_pagamento_anterior)

            # Atualiza o fator_4_anterior e data_pagamento_anterior
            fator_4_anterior = fator_4

            # No mês 0, pula cálculos de pagamentos, mas armazena os resultados básicos
            if mes_atual == 0:
                resultados.append({
                    "Mês": mes_atual,
                    "Parcela": "N/A",
                    "Data Vencimento": "N/A",
                    "DUP": dup,
                    "DUT": dut,
                    "Fator 1": fator_1,
                    "Fator 2": fator_2,
                    "Fator 3": fator_3,
                    "Fator 4": fator_4,
                    "Amortização Principal": "N/A",
                    "Juros BNDES": "N/A",
                    "Juros BANPARA": "N/A",
                    "Parcela Total": "N/A",
                    "Saldo Devedor": round(self.saldo_devedor, 2)
                })
                mes_atual += 1
                continue

            # Verifica os dados de pagamento (juros e/ou amortização)
            pagamento_info = self.verificar_data_pagamento(mes_atual)

            # Define data de vencimento e contador de parcelas
            data_vencimento = None
            contador = None
            if pagamento_info:
                data_vencimento = self.calcula_proxima_data_util(
                    self.data_contratacao + relativedelta(months=mes_atual)
                )
                contador = pagamento_info["numero_parcela"] if pagamento_info["pagar_amortizacao"] else None

            # Calcula amortização principal e atualiza saldo devedor
            amortizacao_principal = None
            if pagamento_info and pagamento_info["pagar_amortizacao"]:
                amortizacao_principal = self.calcula_amortizacao_principal()

            # Calcula juros BNDES e BANPARA
            juros_bndes = self.calcular_juros_bndes(data_vencimento, self.saldo_devedor, fator_4)
            juros_banpara = self.calcular_juros_banpara(data_vencimento, self.saldo_devedor, fator_4)

            # Calcula o valor total da parcela
            valor_parcela = None
            if data_vencimento:
                valor_parcela = round((amortizacao_principal or 0) + juros_bndes + juros_banpara, 2)

            # Armazena os resultados
            resultados.append({
                "Mês": mes_atual,
                "Parcela": contador if contador else "N/A",
                "Data Vencimento": data_vencimento.strftime('%d/%m/%Y') if data_vencimento else "N/A",
                "DUP": dup,
                "DUT": dut,
                "Fator 1": fator_1,
                "Fator 2": fator_2,
                "Fator 3": fator_3,
                "Fator 4": fator_4,
                "Amortização Principal": round(amortizacao_principal, 2) if amortizacao_principal else "N/A",
                "Juros BNDES": juros_bndes,
                "Juros BANCO": juros_banpara,
                "Parcela Total": valor_parcela if valor_parcela else "N/A",
                "Saldo Devedor": round(self.saldo_devedor, 2)
            })

            # Exibe dados na tabela
            if pagamento_info and pagamento_info["pagar_amortizacao"]:
                self.atualizar_saldo_devedor(amortizacao_principal)

            # Interrompe o loop ao atingir o número máximo de parcelas
            if pagamento_info and pagamento_info["pagar_amortizacao"] and contador == self.quantidade_prestacoes:
                break

            mes_atual += 1

        # Exibe os resultados no formato tabular
        print(tabulate(resultados, headers="keys", tablefmt="grid"))

        # Exporta para CSV se solicitado
        if exportar_csv:
            import pandas as pd
            df = pd.DataFrame(resultados)
            df.to_csv("simulador_sudes_resultados.csv", index=False)
            print("\nResultados exportados para 'simulador_sudes_resultados.csv'.")

    def proxima_data_ipca(self, data_input):
        """
        Retorna a próxima data de referência para o IPCA com base na data fornecida.
        """
        if isinstance(data_input, str):
            data_input = datetime.strptime(data_input, "%Y-%m-%d")

        ano = data_input.year
        mes = data_input.month

        if data_input.day == 15:
            dia_referencia = data_input.day
        elif data_input.day >= 15:
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1
            dia_referencia = 15
        else:
            mes -= 1
            if mes < 1:
                mes = 12
                ano -= 1
            dia_referencia = 15

        return datetime(ano, mes, dia_referencia)

    def calcula_proxima_data_util(self, data_input):
        """
        Calcula a próxima data útil com base na data ajustada de `proxima_data_ipca`,
        iniciando a busca de dias úteis a partir do dia 15.

        Parâmetros:
        - data_input (datetime): Data base para o cálculo da próxima data IPCA.

        Retorna:
        - datetime: Data ajustada para o próximo dia útil.
        """
        # Obtém a data ajustada de IPCA, que será a nova referência
        data_ipca = self.proxima_data_ipca(data_input)

        # Ajusta a data para o próximo dia útil, começando a partir da data IPCA
        while data_ipca.weekday() >= 5 or data_ipca.date() in self.feriados:
            data_ipca += timedelta(days=1)

        return data_ipca

    def verificar_data_pagamento(self, mes_atual):
        """
        Verifica se o mês atual é uma data de pagamento, considerando:
        - Durante a carência: Apenas pagamentos de juros com base em `periodic_juros`.
        - Após a carência: Pagamentos de amortização e juros conforme `periodic_amortizacao`.

        Parâmetros:
        - mes_atual (int): Número do mês atual no ciclo do financiamento.

        Retorna:
        - dict: Dicionário com indicações de pagamento de juros, amortização, e o número da parcela,
                ou None se não houver pagamento devido no mês atual.
        """
        # Inicializa dicionário para informações de pagamento
        pagamento_info = {
            "pagar_juros": False,
            "pagar_amortizacao": False,
            "numero_parcela": None
        }

        if mes_atual == 0:
            # No mês 0, nenhum pagamento deve ser feito
            return None

        if mes_atual <= self.carencia:
            # Durante a carência, verifica apenas a periodicidade de pagamento de juros
            if mes_atual % self.periodic_juros == 0:
                pagamento_info["pagar_juros"] = True

        else:
            # Após a carência
            if (mes_atual - self.carencia) % self.periodic_amortizacao == 0:
                # Verifica se o mês atual é um mês de pagamento de amortização
                pagamento_info["pagar_amortizacao"] = True
                pagamento_info["pagar_juros"] = True
                # Calcula o número da parcela
                pagamento_info["numero_parcela"] = (mes_atual - self.carencia) // self.periodic_amortizacao

        # Se nenhum pagamento é devido no mês atual, retorna None
        if not pagamento_info["pagar_juros"] and not pagamento_info["pagar_amortizacao"]:
            return None

        return pagamento_info

    def calcula_dut(self, data_aniversario_anterior, data_aniversario_subsequente):
        """
        Calcula o número de dias úteis entre duas datas de aniversário (DUT).

        Parâmetros:
        - data_aniversario_anterior (datetime): Data de Aniversário anterior (inclusive).
        - data_aniversario_subsequente (datetime): Próxima Data de Aniversário (exclusive).

        Retorna:
        - int: Número de dias úteis (DUT) entre as datas.
        """
        data_atual = to_datetime(data_aniversario_anterior).date()
        data_fim = to_datetime(data_aniversario_subsequente).date()
        dias_uteis = 0

        while data_atual < data_fim:
            if data_atual.weekday() < 5 and data_atual not in self.feriados:
                dias_uteis += 1
            data_atual += timedelta(days=1)
        return dias_uteis

    def calcula_dup(self, data_inicio, data_calculo, data_aniversario_anterior, data_aniversario_subsequente):
        """
        Calcula o número de dias úteis entre as datas, limitado ao valor de DUT.

        Parâmetros:
        - data_inicio (datetime): Data de Desembolso para o primeiro mês de atualização ou a
          data de aniversário anterior para os meses subsequentes (inclusive).
        - data_calculo (datetime): Data de cálculo (exclusive).
        - data_aniversario_anterior (datetime): Data de Aniversário anterior.
        - data_aniversario_subsequente (datetime): Próxima Data de Aniversário.

        Retorna:
        - int: Número de dias úteis (DUP), limitado ao valor de DUT.
        """
        # Calcula o DUT (dias úteis entre aniversários)
        dut = self.calcula_dut(data_aniversario_anterior, data_aniversario_subsequente)

        # Determina a menor data final entre data_calculo e data_aniversario_subsequente
        data_final = min(to_datetime(data_calculo), to_datetime(data_aniversario_subsequente))

        # Conta os dias úteis entre data_inicio e data_final (exclusive)
        dias_uteis = 0
        data_atual = to_datetime(data_inicio).date()
        data_final = data_final.date()

        while data_atual < data_final:
            if data_atual.weekday() < 5 and data_atual not in self.feriados:
                dias_uteis += 1
            data_atual += timedelta(days=1)

        # Limita o DUP ao DUT
        return min(dias_uteis, dut)

    def calcular_fatores(self, dup, dut, fator_4_anterior=None, data_pagamento_anterior=None):
        """
        Calcula os quatro fatores necessários para o financiamento do BNDES.

        Parâmetros:
        - dup (int): Número de dias úteis compreendidos entre as datas definidas.
        - dut (int): Número de dias úteis entre as datas de aniversário.
        - fator_4_anterior (float, opcional): Valor do fator_4 da parcela anterior (para o cálculo cumulativo de fator_4).

        Retorna:
        - tuple: (fator_1, fator_2, fator_3, fator_4), com cada fator calculado com precisão de 16 casas decimais.
        """
        # Cálculo dos fatores
        fator_1 = round((1 + self.ipca_mensal / 100) ** (dup / dut), 16)
        fator_2 = round((1 + self.juros_prefixados_aa / 100) ** (dup / 252), 16)
        fator_3 = round((1 + self.spread_bndes_aa / 100) ** (dup / 252), 16)

        # Fator 4 depende de fator_4_anterior para parcelas subsequentes
        # Lógica para calcular fator_4 com base na data de pagamento anterior
        if data_pagamento_anterior is None and fator_4_anterior:
            fator_4 = fator_1 * fator_2 * fator_3 * fator_4_anterior
        else:
            fator_4 = fator_1 * fator_2 * fator_3

        # Retorna os fatores com 16 casas decimais de precisão
        return fator_1, fator_2, fator_3, round(fator_4, 16)

    def calcula_amortizacao_principal(self):
        """
        Calcula a amortização principal com base no saldo devedor atual e no número de parcelas restantes.

        Retorna:
        - Decimal: O valor da amortização principal para a parcela atual.
        """
        amortizacao_principal = self.saldo_devedor / self.quantidade_prestacoes_restantes
        return amortizacao_principal

    def atualizar_saldo_devedor(self, amortizacao_principal):
        """
        Atualiza o saldo devedor após a amortização principal e decrementa o número de parcelas restantes.

        Parâmetros:
        - amortizacao_principal (Decimal): O valor da amortização principal a ser subtraído do saldo devedor.
        """
        self.saldo_devedor -= amortizacao_principal
        self.quantidade_prestacoes_restantes -= 1

    def calcular_juros_bndes(self, data_pagamento, saldo_devedor, fator_4):
        """
        Calcula os juros do BNDES apenas quando existe uma data de pagamento.

        Parâmetros:
        - data_pagamento (datetime or None): Data de pagamento para o mês atual.
        - saldo_devedor (float): Saldo devedor atual.
        - fator_4 (float): Fator 4 calculado para o mês atual.

        Retorna:
        - float: Juros do BNDES arredondado para 2 casas decimais se há pagamento, ou 0 caso contrário.
        """
        # Se não há data de pagamento, retorna 0 para juros
        if data_pagamento is None:
            return 0

        # Calcula os juros como saldo_devedor * (fator_4 - 1) e arredonda para 2 casas decimais
        juros_bndes = round(saldo_devedor * (fator_4 - 1), 2)
        return juros_bndes

    def calcular_juros_banpara(self, data_pagamento, saldo_devedor, fator_4):
        """
        Calcula os juros do BANPARA apenas quando existe uma data de pagamento.

        Parâmetros:
        - data_pagamento (datetime or None): Data de pagamento para o mês atual.
        - saldo_devedor (float): Saldo devedor atual.
        - fator_4 (float): Fator 4 calculado para o mês atual.

        Retorna:
        - float: Juros do BANPARA arredondado para 2 casas decimais se há pagamento, ou 0 caso contrário.
        """
        # Se não há data de pagamento, retorna 0 para juros
        if data_pagamento is None:
            return 0

        # Calcula o fator BANPARA considerando apenas o spread BANPARA
        fator_banpara = (1 + self.spread_banpara_am)

        # Calcula os juros como saldo_devedor * (fator_banpara - 1) e arredonda para 2 casas decimais
        juros_banpara = round(saldo_devedor * (fator_banpara - 1), 2)
        return juros_banpara
