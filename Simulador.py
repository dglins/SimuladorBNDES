from pandas import to_datetime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from lista_feriados import feriados

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
        Exibe os dados de pagamento para cada mês até que o contador atinja o número máximo de parcelas (self.quantidade_prestacoes).
        """
        mes_atual = 0
        fator_4_anterior = None  # Inicializa o fator_4 para a primeira parcela
        data_pagamento_anterior = None
        while True:
            contador = self.contador_mes(mes_atual)
            data_vencimento = self.verificar_data_vencimento(mes_atual) if contador is not None else None

            # Determina as datas de aniversário (referências de cálculo) para cada mês
            data_aniversario_anterior = self.proxima_data_ipca(self.data_contratacao + relativedelta(months=mes_atual))
            data_aniversario_subsequente = self.proxima_data_ipca(
                self.data_contratacao + relativedelta(months=mes_atual + 1))

            # Calcula DUT entre aniversários
            dut = self.calcula_dut(data_aniversario_anterior, data_aniversario_subsequente)

            # Define data_inicio e data_final para cálculo de DUP
            data_inicio = self.data_contratacao if mes_atual == 0 else data_aniversario_anterior
            data_calculo = self.data_contratacao + relativedelta(months=mes_atual + 1)

            # Calcula DUP, limitado a DUT
            dup = self.calcula_dup(data_inicio, data_calculo, data_aniversario_anterior, data_aniversario_subsequente)

            # FATORES
            fator_1, fator_2, fator_3, fator_4 = self.calcular_fatores(dup, dut, fator_4_anterior,data_pagamento_anterior)

            # Atualiza fator_4_anterior com o valor atual de fator_4 para o próximo mês
            fator_4_anterior = fator_4
            data_pagamento_anterior = data_vencimento

            # Calcula a amortização principal e atualiza o saldo devedor
            amortizacao_principal = self.calcula_amortizacao_principal() if contador else None


            # Calcula os juros BNDES
            juros_bndes = self.calcular_juros_bndes(data_vencimento, self.saldo_devedor, fator_4)
            # Calcula os juros BANPARA
            juros_banpara = self.calcular_juros_banpara(data_vencimento, self.saldo_devedor, fator_4)
            # Calcula valor da parcela
            valor_parcela = amortizacao_principal + juros_bndes + juros_banpara  if contador else None

            # Output teste
            print(f"\033[1;32mMês {mes_atual + 1}:\033[0m "  # Verde para o mês
                  f"\033[1;34mParcela: {contador}\033[0m "  # Azul para o contador de parcelas
                  f"\033[1;33mData Venc.: {data_vencimento}\033[0m "  # Amarelo para a data de vencimento
                  f"\033[1;35mDUP: {dup} DUT: {dut}\033[0m "  # Magenta para DUT e DUP
                  f"\033[1;31mJuros BNDES: {juros_bndes} Juros BANPARA: {juros_banpara}\033"
                  f"\033[1;33m Parcela Total: {valor_parcela}\033[0m"
                  f"\033[1;25m Amortização Principal: {amortizacao_principal if amortizacao_principal is not None else 'N/A'}:\033[0m "
                  f"\033[1;38mSaldo Devedor: {round(self.saldo_devedor, 2)}:\033[0m"
                  )  # Ciano para os fatores

            # Verifica se o contador de parcelas a quantidade máxima de parcelas e interrompe o loop
            if amortizacao_principal is not None:
                self.atualizar_saldo_devedor(amortizacao_principal)
            if contador == self.quantidade_prestacoes:
                break
            mes_atual += 1

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

    def contador_mes(self, mes_atual):
        """
        Calcula o contador de parcelas a serem pagas, iniciando em 1 após o período de carência
        e incrementando apenas nos meses que correspondem ao período de pagamento de amortização.

        Parâmetros:
        - mes_atual (int): Número do mês atual no ciclo do financiamento.

        Retorna:
        - int ou None: O contador de parcelas a serem pagas ou None se ainda estiver na carência.
        """
        # Se estamos na carência, o contador permanece como None
        if mes_atual <= self.carencia:
            return None

        # Fora da carência, o contador avança apenas nos meses de pagamento de amortização
        if (mes_atual - self.carencia - 1) % self.periodic_amortizacao == 0:
            return (mes_atual - self.carencia - 1) // self.periodic_amortizacao + 1

        # Caso contrário, não é um mês de pagamento e o contador permanece None
        return None

    def calcular_parcelas_restantes(self, contador):
        """
        Calcula o número de parcelas restantes com base no contador de parcelas a serem pagas.

        Parâmetros:
        - contador (int): O contador de parcelas a serem pagas.

        Retorna:
        - int ou None: O número de parcelas restantes ou None se o contador for None.
        """
        if contador is None:
            return None
        return self.quantidade_prestacoes - contador

    def verificar_data_vencimento(self, mes_atual):
        """
        Verifica se o mês atual corresponde a um mês de pagamento e, se for, calcula e retorna a data de vencimento,
        já ajustada para o próximo dia útil com `calcula_proxima_data_util`.

        Parâmetros:
        - mes_atual (int): Número do mês atual no ciclo do financiamento.

        Retorna:
        - datetime ou None: A data de vencimento (próxima data útil) se houver pagamento,
          ou None se não for um mês de pagamento.
        """
        # Verifica o contador de meses de pagamento para o mês atual
        contador = self.contador_mes(mes_atual)

        # Se o contador for None, significa que não é um mês de pagamento, então retorna None
        if contador is None:
            return None

        # Calcula a data de referência para o mês atual
        data_referencia = self.data_contratacao + relativedelta(months=mes_atual+1)

        # Retorna a data da próxima data útil baseada na data de referência para o mês atual
        return self.calcula_proxima_data_util(data_referencia)

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





# Inicializa o simulador com parâmetros
simulador = SimuladorSudes(
    data_contratacao="15/10/2024",      # Data de contratação do financiamento
    valor_liberado=200000.00,           # Valor liberado (em reais)
    carencia=3,                         # Período de carência em meses
    periodic_juros=4,                   # Periodicidade do pagamento de juros (meses)
    prazo_amortizacao=20,               # Prazo de amortização (meses)
    periodic_amortizacao=2,             # Periodicidade de pagamento de amortização (meses)
    juros_prefixados_aa=6.31,           # Taxa de juros prefixados anual (% a.a.)
    ipca_mensal=0.44,                   # Variação mensal do IPCA (% a.m.)
    spread_bndes_aa=1.15,               # Spread do BNDES anual (% a.a.)
    spread_banpara_aa=5.75              # Spread do BANPARA anual (% a.a.)
)



print("Contagem de Meses de Pagamento e Datas de Vencimento:\n\n")
simulador.exibir_dados_pagamento()