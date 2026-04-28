import os
import sys
import unittest

sys.path.insert(0, os.path.abspath('online-food-delivery-system/backend'))

from utils.password_helper import hash_password, needs_rehash, verify_password


class PasswordHelperTests(unittest.TestCase):
    def test_hash_and_verify_password(self):
        hashed = hash_password('SafePass123')
        self.assertTrue(hashed.startswith('$2'))
        self.assertTrue(verify_password(hashed, 'SafePass123'))
        self.assertFalse(verify_password(hashed, 'WrongPass123'))
        self.assertFalse(needs_rehash(hashed))


if __name__ == '__main__':
    unittest.main()
