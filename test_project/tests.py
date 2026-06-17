#!/usr/bin/env python3
"""
Unit tests for utils module
"""

import unittest
from utils import add, multiply, divide

class TestUtils(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

if __name__ == '__main__':
    unittest.main()
