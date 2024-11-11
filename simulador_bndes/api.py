# api.py
import requests
import json

def obter_tlp():
    """
    Obtém o valor mais recente da TLP via API do Banco Central.
    """
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.27572/dados/ultimos/1?formato=json"
        response = requests.get(url)
        if response.status_code == 200:
            dados = json.loads(response.text)
            return float(dados[0]['valor'])
        return 1.15  # Valor padrão em caso de falha
    except Exception as e:
        print(f"Erro ao buscar TLP: {e}")
        return 1.15

def obter_ipca():
    """
    Obtém o valor mais recente do IPCA via API do Banco Central.
    """
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/1?formato=json"
        response = requests.get(url)
        if response.status_code == 200:
            dados = json.loads(response.text)
            return float(dados[0]['valor'])
        return 0.44  # Valor padrão em caso de falha
    except Exception as e:
        print(f"Erro ao buscar IPCA: {e}")
        return 0.44
