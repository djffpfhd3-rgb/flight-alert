import unittest
from trinity_check import TARGET, classify

class ClassificationTests(unittest.TestCase):
    def observation(self):
        return {'target': dict(TARGET), 'fares': [
            {'type': t, 'disabled': True, 'sold_out': True}
            for t in ('EventFare', 'SmartFare', 'NormalFare')]}

    def test_sold_out_requires_all_three_explicit_fares(self):
        o = self.observation()
        self.assertEqual(classify(o), 'SOLD_OUT')
        o['fares'].pop()
        self.assertEqual(classify(o), 'UNKNOWN')

    def test_wrong_date_is_not_a_seat_alert(self):
        o = self.observation()
        o['target']['date'] = '2026-11-09'
        self.assertEqual(classify(o), 'UNKNOWN')

    def test_price_alone_is_not_availability(self):
        o = self.observation()
        o['fares'][0].update(disabled=False, sold_out=False, positive_price=True)
        self.assertEqual(classify(o), 'UNKNOWN')
        o['fares'][0]['selection_verified'] = True
        self.assertEqual(classify(o), 'AVAILABLE')

    def test_empty_or_error_is_unknown(self):
        self.assertEqual(classify({}), 'UNKNOWN')

if __name__ == '__main__':
    unittest.main()
