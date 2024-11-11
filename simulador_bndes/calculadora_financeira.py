class CalculadoraFinanceira:
    @staticmethod
    def calcular_fatores(ipca_mensal, juros_prefixados_aa, spread_bndes_aa, dup, dut, fator_4_anterior=None):
        fator_1 = (1 + ipca_mensal / 100) ** (dup / dut)
        fator_2 = (1 + juros_prefixados_aa / 100) ** (dup / 252)
        fator_3 = (1 + spread_bndes_aa / 100) ** (dup / 252)
        fator_4 = fator_1 * fator_2 * fator_3 if fator_4_anterior is None else fator_4_anterior * fator_1 * fator_2 * fator_3
        return round(fator_1, 16), round(fator_2, 16), round(fator_3, 16), round(fator_4, 16)

    @staticmethod
    def calcular_juros_bndes(saldo_devedor, fator_4):
        """
        Calcula os juros do BNDES com base no saldo devedor e no fator financeiro.

        Parâmetros:
        - saldo_devedor (float): Saldo devedor atual.
        - fator_4 (float): Fator acumulado calculado para o mês.

        Retorna:
        - float: Valor dos juros BNDES arredondado para 2 casas decimais.
        """
        # Calcula os juros como saldo_devedor * (fator_4 - 1)
        juros_bndes = saldo_devedor * (fator_4 - 1)
        return round(juros_bndes, 2)

    @staticmethod
    def calcular_juros_banco(saldo_devedor, spread_banco_am):
        """
        Calcula os juros do banco com base no saldo devedor e no spread mensal do banco.

        Parâmetros:
        - saldo_devedor (float): Saldo devedor atual.
        - spread_banco_am (float): Spread do banco ao mês.

        Retorna:
        - float: Valor dos juros do banco arredondado para 2 casas decimais.
        """
        fator_banco = (1 + spread_banco_am)
        juros_banco = saldo_devedor * (fator_banco - 1)
        return round(juros_banco, 2)

    @staticmethod
    def exportar_csv(resultados, arquivo):
        import pandas as pd
        df = pd.DataFrame(resultados)
        df.to_csv(arquivo, index=False)
        print(f"Resultados exportados para {arquivo}.")
