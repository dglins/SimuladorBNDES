# utils.py
from datetime import datetime, timedelta

def proxima_data_ipca(data_input):
    """
    Retorna a próxima data de referência para o IPCA com base na data fornecida.
    """
    ano, mes = data_input.year, data_input.month
    if data_input.day >= 15:
        mes += 1
        if mes > 12:
            mes, ano = 1, ano + 1
    else:
        mes -= 1
        if mes < 1:
            mes, ano = 12, ano - 1
    return datetime(ano, mes, 15)

def calcula_proxima_data_util(data, feriados):
    """
    Calcula a próxima data útil com base na data fornecida.
    """
    while data.weekday() >= 5 or data.date() in feriados:
        data += timedelta(days=1)
    return data
