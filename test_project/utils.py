"""
Utility functions for test project

This module provides basic math functions.
"""

def add(a, b):
    """Add two numbers and return the result"""
    return a + b

def multiply(a, b):
    """Multiply two numbers and return the result"""
    return a * b

def divide(a, b):
    """Divide two numbers and return the result
    
    Args:
        a: Numerator
        b: Denominator
        
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
