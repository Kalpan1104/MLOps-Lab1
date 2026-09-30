import pytest
from src import calculator

def test_func1():
    assert calculator.func1(2,5) == 7
    assert calculator.func1(5,1) == 6
    assert calculator.func1 (-1, -3) == -4
    assert calculator.func1 (-1, 1) == 0


def test_func2():
    assert calculator.func2(2, 4) == -2
    assert calculator.func2(5,0) == 5
    assert calculator.func2 (-1, 2) == -3
    assert calculator.func2 (-1, -1) == 0

def test_func3():
    assert calculator.func3(2, 3) == 6
    assert calculator.func3(5,0) == 0
    assert calculator.func3 (-1, 1) == -1
    
    assert calculator.func3 (-1, -1) == 1

def test_func4():
    assert calculator.func4(2, 3, 5) == 10
    assert calculator.func4(5,0, -1) == 4
    assert calculator.func4 (-1, -1, -1) == -3
    
    assert calculator.func4 (-1, -1, 100) == 98