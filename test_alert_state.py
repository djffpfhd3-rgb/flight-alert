import unittest
from alert_state import advance, should_notify

class StateTests(unittest.TestCase):
    def test_unknown_does_not_rearm_alert(self):
        state = advance({}, 'AVAILABLE', delivered=True)
        state = advance(state, 'UNKNOWN')
        self.assertFalse(should_notify(state, 'AVAILABLE'))

    def test_sold_out_rearms(self):
        state = advance({}, 'AVAILABLE', delivered=True)
        state = advance(state, 'SOLD_OUT')
        self.assertTrue(should_notify(state, 'AVAILABLE'))

    def test_failed_delivery_retries(self):
        state = advance({}, 'SOLD_OUT')
        state = advance(state, 'AVAILABLE', delivered=False)
        self.assertTrue(should_notify(state, 'AVAILABLE'))

    def test_no_sold_out_or_unknown_notification(self):
        for status in ['SOLD_OUT', 'UNKNOWN']:
            self.assertFalse(should_notify({}, status))

if __name__ == '__main__':
    unittest.main()
