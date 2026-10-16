import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'monitor'))
from check import parse_page,normalize_price
class Tests(unittest.TestCase):
    def test_price(self):
        self.assertEqual(normalize_price('€ 199,95'),199.95)
        self.assertEqual(normalize_price('1.299,00'),1299)
    def test_product(self):
        html='<script type="application/ld+json">{"@type":"Product","name":"ETB","offers":{"@type":"Offer","price":"89.99","priceCurrency":"EUR","availability":"https://schema.org/InStock"}}</script>'
        self.assertEqual(parse_page(html)['stock'],'in_stock')
        self.assertEqual(parse_page(html)['price'],89.99)
    def test_no_trust(self):
        self.assertEqual(parse_page('<p>€ 2,00 In stock</p>')['status'],'unverifiable')
if __name__=='__main__': unittest.main()
