import unittest
from datetime import datetime
from simulador_bndes.utils import proxima_data_ipca, calcula_proxima_data_util

class TestUtils(unittest.TestCase):
    def test_proxima_data_ipca(self):
        data = datetime(2024, 11, 14)
        resultado = proxima_data_ipca(data)
        self.assertEqual(resultado, datetime(2024, 10, 15))

    def test_calcula_proxima_data_util(self):
        feriados = [datetime(2024, 12, 25).date()]
        data = datetime(2024, 12, 25)
        resultado = calcula_proxima_data_util(data, feriados)
        self.assertNotEqual(resultado.date(), datetime(2024, 12, 25).date())
        self.assertEqual(resultado.date().weekday() < 5, True)

if __name__ == "__main__":
    unittest.main()
