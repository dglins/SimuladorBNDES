import unittest
from simulador_bndes.simulador_bndes import SimuladorBNDES

class TestSimuladorBNDES(unittest.TestCase):
    def setUp(self):
        self.simulador = SimuladorBNDES(
            data_contratacao="09/10/2024",
            valor_liberado=200000.00,
            carencia=3,
            periodic_juros=1,
            prazo_amortizacao=10,
            periodic_amortizacao=3,
            juros_prefixados_aa=6.31,
            ipca_mensal=0.44,
            spread_bndes_aa=1.15,
            spread_banco_aa=5.75
        )

    def test_inicializacao(self):
        self.assertEqual(self.simulador.valor_liberado, 200000)
        self.assertEqual(self.simulador.carencia, 3)

    def test_calculo_amortizacao(self):
        self.simulador.saldo_devedor = 100000
        amortizacao = self.simulador.calcular_amortizacao_principal()
        self.assertEqual(amortizacao, 10000)

    def test_exibir_dados_pagamento(self):
        resultados = self.simulador.exibir_dados_pagamento(exportar_csv=False)
        self.assertGreater(len(resultados), 0)

if __name__ == "__main__":
    unittest.main()
