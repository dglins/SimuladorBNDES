import unittest
from simulador_bndes.calculos import calcular_amortizacao_principal, calcular_juros_bndes, calcular_juros_banco

class TestCalculos(unittest.TestCase):
    def test_calcular_amortizacao_principal(self):
        saldo_devedor = 100000
        quantidade_prestacoes = 10
        amortizacao = calcular_amortizacao_principal(saldo_devedor, quantidade_prestacoes)
        self.assertEqual(amortizacao, 10000)

    def test_calcular_juros_bndes(self):
        saldo_devedor = 100000
        fator_4 = 1.02
        juros = calcular_juros_bndes(saldo_devedor, fator_4)
        self.assertEqual(juros, 2000)

    def test_calcular_juros_banco(self):
        saldo_devedor = 100000
        spread_banco_am = 0.005
        juros = calcular_juros_banco(saldo_devedor, spread_banco_am)
        self.assertEqual(juros, 500)

if __name__ == "__main__":
    unittest.main()
