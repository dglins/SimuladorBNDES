import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from lista_feriados import feriados
from gerenciador_datas import GerenciadorDatas
from calculadora_financeira import CalculadoraFinanceira
from gerenciador_apis import GerenciadorAPIs

class SimuladorBNDES:
    def __init__(self, data_contratacao: str, valor_liberado: float, carencia: int,
                 periodic_juros: int, prazo_amortizacao: int,
                 periodic_amortizacao: int, juros_prefixados_aa: float,
                 ipca_mensal: float = None, spread_bndes_aa: float = None, spread_banco_aa: float = None):
        # Inicializa parâmetros principais
        self.amortizacao_a_aplicar = 0  # Inicializa com zero
        self.data_contratacao = datetime.strptime(data_contratacao, "%d/%m/%Y")
        self.valor_liberado = valor_liberado
        self.saldo_devedor = valor_liberado
        self.carencia = carencia
        self.periodic_juros = periodic_juros
        self.prazo_amortizacao = prazo_amortizacao
        self.periodic_amortizacao = periodic_amortizacao
        self.juros_prefixados_aa = juros_prefixados_aa

        # Instancia classes auxiliares
        self.datas = GerenciadorDatas(feriados)
        self.apis = GerenciadorAPIs()
        self.calculadora = CalculadoraFinanceira()

        # Busca valores da TLP e IPCA automaticamente, se não fornecidos
        self.ipca_mensal = ipca_mensal if ipca_mensal is not None else self.apis.obter_ipca()
        self.spread_bndes_aa = spread_bndes_aa if spread_bndes_aa is not None else self.apis.obter_tlp()
        self.spread_banco_aa = spread_banco_aa if spread_banco_aa is not None else 5.75  # Default

        # Calcula a quantidade de prestações e converte taxas anuais para mensais
        self.quantidade_prestacoes = math.ceil(prazo_amortizacao / periodic_amortizacao)
        self.quantidade_prestacoes_restantes = prazo_amortizacao / periodic_amortizacao
        self.juros_prefixados_am = (1 + juros_prefixados_aa / 100) ** (1 / 12) - 1
        self.spread_bndes_am = (1 + self.spread_bndes_aa / 100) ** (1 / 12) - 1
        self.spread_banco_am = (1 + self.spread_banco_aa / 100) ** (1 / 12) - 1

    def verificar_data_pagamento(self, mes_atual):
        """
        Verifica se o mês atual é uma data de pagamento, considerando:
        - Durante a carência: Apenas pagamentos de juros com base em `periodic_juros`.
        - Após a carência: Pagamentos de amortização e juros conforme `periodic_amortizacao`.

        Parâmetros:
        - mes_atual (int): Número do mês atual no ciclo do financiamento.

        Retorna:
        - dict: Indicações de pagamento de juros, amortização e o número da parcela,
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

    def aplicar_amortizacao(self):
        """
        Aplica a amortização acumulada ao saldo devedor no início do mês, se houver.
        """
        if hasattr(self, 'amortizacao_a_aplicar') and self.amortizacao_a_aplicar > 0:
            self.saldo_devedor -= self.amortizacao_a_aplicar
            self.quantidade_prestacoes_restantes -= 1
            self.amortizacao_a_aplicar = 0

    def exibir_dados_pagamento(self, exportar_csv=False):
        """
        Exibe os dados de pagamento em formato tabular e opcionalmente exporta para CSV.

        Parâmetros:
        - exportar_csv (bool): Se True, exporta os resultados para um arquivo CSV.

        Retorna:
        - list: Lista de dicionários com os detalhes de cada mês.
        """
        resultados = []
        mes_atual = 0
        fator_4_anterior = None
        data_pagamento_anterior = None

        while mes_atual <= self.quantidade_prestacoes:
            self.aplicar_amortizacao()
            # Determina as datas de aniversário
            data_aniversario_anterior = self.datas.calcular_proxima_data_util(
                self.data_contratacao + relativedelta(months=mes_atual - 1)
            ) if mes_atual > 0 else self.data_contratacao
            data_aniversario_subsequente = self.datas.calcular_proxima_data_util(
                self.data_contratacao + relativedelta(months=mes_atual)
            )

            # Calcula DUT e DUP
            dut = self.datas.calcula_dut(data_aniversario_anterior, data_aniversario_subsequente)
            data_inicio = self.data_contratacao if mes_atual == 0 else data_aniversario_anterior
            dup = self.datas.calcula_dup(
                data_inicio=data_inicio,
                data_calculo=self.data_contratacao + relativedelta(months=mes_atual + 1),
                data_aniversario_anterior=data_aniversario_anterior,
                data_aniversario_subsequente=data_aniversario_subsequente
            )

            # Calcula os fatores financeiros
            fator_1, fator_2, fator_3, fator_4 = self.calculadora.calcular_fatores(
                self.ipca_mensal, self.juros_prefixados_aa, self.spread_bndes_aa, dup, dut, fator_4_anterior
            )
            fator_4_anterior = fator_4

            # Determina o pagamento de juros e/ou amortização
            pagamento_info = self.verificar_data_pagamento(mes_atual)

            if pagamento_info and pagamento_info["pagar_amortizacao"]:
                # Calcula a amortização principal e atualiza saldo devedor
                amortizacao_principal = self.calculadora.calcula_amortizacao_principal(
                    self.saldo_devedor, self.quantidade_prestacoes_restantes
                )
                self.saldo_devedor -= amortizacao_principal
                self.quantidade_prestacoes_restantes -= 1
            else:
                amortizacao_principal = 0

            # Calcula os juros BNDES e banco
            juros_bndes = self.calculadora.calcular_juros_bndes(
                self.saldo_devedor, fator_4
            )
            juros_banco = self.calculadora.calcular_juros_banco(
                self.saldo_devedor, self.spread_banco_am
            )

            # Calcula o valor total da parcela
            parcela_total = amortizacao_principal + juros_bndes + juros_banco

            # Salva os resultados do mês atual
            resultados.append({
                "Mês": mes_atual,
                "DUP": dup,
                "DUT": dut,
                "Parcela": pagamento_info["numero_parcela"] if pagamento_info else "-",
                "Data Vencimento": data_aniversario_subsequente.strftime('%d/%m/%Y'),
                "Amortização Principal": round(amortizacao_principal, 2),
                "Juros BNDES": round(juros_bndes, 2),
                "Juros Banco": round(juros_banco, 2),
                "Parcela Total": round(parcela_total, 2),
                "Saldo Devedor": round(self.saldo_devedor, 2)
            })

            # Incrementa o mês
            mes_atual += 1

            # Interrompe o loop ao finalizar as prestações
            if self.saldo_devedor <= 0:
                break

        # Exporta os resultados para CSV, se solicitado
        if exportar_csv:
            self.calculadora.exportar_csv(resultados, "simulador_resultados.csv")

        return resultados

