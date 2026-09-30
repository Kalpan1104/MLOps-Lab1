import sys
import os
import unittest
from src import calculator


class TestCalculator(unittest.TestCase):

    def test_func1(self):
        self.assertEqual(calculator.func1(2, 3), 5)
        self.assertEqual(calculator.func1(5, 0), 5)
        
        self.assertEqual(calculator.func1(-1, 1), 0)
        self.assertEqual(calculator.func1(-1, -3), -4)

    def test_func2(self):
        self.assertEqual(calculator.func2(2, 4), -2)
        self.assertEqual(calculator.func2(5, 0), 5)
        self.assertEqual(calculator.func2(-1, 2), -3)
        self.assertEqual(calculator.func2(-1, -1), 0)

    def test_func3(self):
        self.assertEqual(calculator.func3(2, 3), 6)
        self.assertEqual(calculator.func3(5, 0), 0)
        self.assertEqual(calculator.func3(-1, 1), -1)
        self.assertEqual(calculator.func3(-1, -1), 1)

    def test_func4(self):
        self.assertEqual(calculator.func4(2, 3, 5), 10)
        self.assertEqual(calculator.func4(5, 0, -1), 4)
        self.assertEqual(calculator.func4(-1, -1, -1), -3)
        self.assertEqual(calculator.func4(-1, -1, 100), 98)



if __name__ == '__main__':
    unittest.main()