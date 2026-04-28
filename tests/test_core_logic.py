import os
import sys
import unittest

sys.path.insert(0, os.path.abspath('online-food-delivery-system/backend'))

from services.order_service import calculate_cart_totals
from utils.validation_helper import ValidationError, validate_email, validate_payment_method


class ValidationAndOrderTests(unittest.TestCase):
    def test_validate_email_rejects_invalid_input(self):
        with self.assertRaises(ValidationError):
            validate_email('not-an-email')

    def test_validate_payment_method_accepts_supported_value(self):
        self.assertEqual(validate_payment_method('upi'), 'upi')

    def test_calculate_cart_totals(self):
        totals = calculate_cart_totals([
            {'price': 120, 'quantity': 2},
            {'price': 90, 'quantity': 1},
        ])
        self.assertEqual(totals['subtotal'], 330)
        self.assertEqual(totals['delivery_fee'], 40)
        self.assertEqual(totals['tax_amount'], 16)
        self.assertEqual(totals['total_amount'], 386)


if __name__ == '__main__':
    unittest.main()
