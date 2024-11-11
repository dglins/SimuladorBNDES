import requests
import json

class GerenciadorAPIs:
    @staticmethod
    def obter_tlp():
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

    @staticmethod
    def obter_ipca():
        try:
            url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/1?formato=json"
            response = requests.get(url)
            if response.status_code == 200:
                dados = json.loads(response.text)
                return float(dados[0]['valor'])
            return 0.44
        except Exception as e:
            print(f"Erro ao buscar IPCA: {e}")
            return 0.44
