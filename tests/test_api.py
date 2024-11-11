import unittest
from simulador_bndes.api import obter_tlp, obter_ipca

class TestAPI(unittest.TestCase):
    def test_obter_tlp(self):
        tlp = obter_tlp()
        self.assertIsInstance(tlp, float)
        self.assertGreater(tlp, 0)  # Valor deve ser positivo

    def test_obter_ipca(self):
        ipca = obter_ipca()
        self.assertIsInstance(ipca, float)
        self.assertGreaterEqual(ipca, 0)  # Valor não deve ser negativo

if __name__ == "__main__":
    unittest.main()
