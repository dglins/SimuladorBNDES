from datetime import datetime, timedelta
from lista_feriados import feriados



class GerenciadorDatas:
    def __init__(self, feriados):
        self.feriados = [datetime.strptime(f, "%d/%m/%Y").date() for f in feriados]

    def proxima_data_ipca(self, data_input):
        """
        Retorna a próxima data de referência para o IPCA com base na data fornecida.
        A data de referência é sempre o dia 15 do mês atual, anterior ou seguinte.

        Parâmetros:
        - data_input (datetime | str): Data de entrada.

        Retorna:
        - datetime: Data de referência para o IPCA.
        """
        if isinstance(data_input, str):
            data_input = datetime.strptime(data_input, "%Y-%m-%d")

        ano, mes = data_input.year, data_input.month

        if data_input.day >= 15:
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1

        return datetime(ano, mes, 15)

    def calcula_proxima_data_util(self, data_input):
        """
        Calcula a próxima data útil com base na data ajustada para o IPCA,
        iniciando a busca de dias úteis a partir do dia 15 do mês.

        Parâmetros:
        - data_input (datetime): Data base para o cálculo.

        Retorna:
        - datetime: Próxima data útil.
        """
        # Obtém a data ajustada para o IPCA
        data_ipca = self.proxima_data_ipca(data_input)

        # Incrementa até encontrar um dia útil
        while data_ipca.weekday() >= 5 or data_ipca.date() in self.feriados:
            data_ipca += timedelta(days=1)

        return data_ipca

    def calcula_dut(self, data_aniversario_anterior, data_aniversario_subsequente):
        """
        Calcula o número de dias úteis entre duas datas de aniversário (DUT).
        Retorna pelo menos 1 para evitar divisão por zero.
        """
        data_atual = data_aniversario_anterior.date()
        data_fim = data_aniversario_subsequente.date()
        dias_uteis = 0

        while data_atual < data_fim:
            if data_atual.weekday() < 5 and data_atual not in self.feriados:
                dias_uteis += 1
            data_atual += timedelta(days=1)

        # Garante que o DUT nunca será zero
        return dias_uteis

    def calcula_dup(self, data_inicio, data_calculo, data_aniversario_anterior, data_aniversario_subsequente):
        """
        Calcula o número de dias úteis entre as datas, limitado ao valor de DUT.

        Parâmetros:
        - data_inicio (datetime): Data de Desembolso ou a data de aniversário anterior.
        - data_calculo (datetime): Data de cálculo (exclusive).
        - data_aniversario_anterior (datetime): Data de Aniversário anterior.
        - data_aniversario_subsequente (datetime): Próxima Data de Aniversário.

        Retorna:
        - int: Número de dias úteis (DUP), limitado ao valor de DUT.
        """
        # Calcula o DUT (dias úteis entre aniversários)
        dut = self.calcula_dut(data_aniversario_anterior, data_aniversario_subsequente)

        # Determina a menor data final entre data_calculo e data_aniversario_subsequente
        data_final = min(data_calculo, data_aniversario_subsequente)

        # Conta os dias úteis entre data_inicio e data_final (exclusive)
        dias_uteis = 0
        data_atual = data_inicio.date()
        data_final = data_final.date()

        while data_atual < data_final:
            if data_atual.weekday() < 5 and data_atual not in self.feriados:
                dias_uteis += 1
            data_atual += timedelta(days=1)

        # Limita o DUP ao DUT
        return min(dias_uteis, dut)