from datetime import datetime, timedelta
from typing import List

class GerenciadorDatas:
    def __init__(self, feriados: List[str]):
        """
        Inicializa o GerenciadorDatas com uma lista de feriados.
        Feriados são convertidos para objetos datetime.date.

        Parâmetros:
        - feriados (List[str]): Lista de feriados no formato "dd/mm/yyyy".
        """
        self.feriados = sorted(
            {datetime.strptime(f, "%d/%m/%Y").date() for f in feriados}
        )

    def adicionar_feriado(self, feriado: str):
        """
        Adiciona um novo feriado à lista.

        Parâmetros:
        - feriado (str): Data no formato "dd/mm/yyyy".
        """
        feriado_date = datetime.strptime(feriado, "%d/%m/%Y").date()
        if feriado_date not in self.feriados:
            self.feriados.append(feriado_date)
            self.feriados.sort()  # Mantém os feriados ordenados

    def verificar_feriado(self, data):
        """
        Verifica se uma data é feriado.

        Parâmetros:
        - data (datetime | date): Data a ser verificada.

        Retorna:
        - bool: True se a data for feriado, False caso contrário.
        """
        if isinstance(data, datetime):  # Converte para `date` se for `datetime`
            data = data.date()
        return data in self.feriados

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
        while data_ipca.weekday() >= 5 or self.verificar_feriado(data_ipca):
            data_ipca += timedelta(days=1)

        return data_ipca

    def calcula_dut(self, data_aniversario_anterior, data_aniversario_subsequente):
        """
        Calcula o número de dias úteis entre duas datas de aniversário (DUT).

        Parâmetros:
        - data_aniversario_anterior (datetime): Data de Aniversário anterior (inclusive).
        - data_aniversario_subsequente (datetime): Próxima Data de Aniversário (exclusive).

        Retorna:
        - int: Número de dias úteis (DUT) entre as datas.
        """
        data_atual = data_aniversario_anterior.date()
        data_fim = data_aniversario_subsequente.date()
        dias_uteis = 0

        while data_atual < data_fim:
            if data_atual.weekday() < 5 and not self.verificar_feriado(data_atual):
                dias_uteis += 1
            data_atual += timedelta(days=1)
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
            if data_atual.weekday() < 5 and not self.verificar_feriado(data_atual):
                dias_uteis += 1
            data_atual += timedelta(days=1)

        # Limita o DUP ao DUT
        return min(dias_uteis, dut)
