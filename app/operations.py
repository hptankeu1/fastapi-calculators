"""Arithmetic operations, selected by name (simple factory)."""
from enum import Enum


class CalculationType(str, Enum):
    add = "add"
    subtract = "subtract"
    multiply = "multiply"
    divide = "divide"


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


OPERATIONS = {
    CalculationType.add: add,
    CalculationType.subtract: subtract,
    CalculationType.multiply: multiply,
    CalculationType.divide: divide,
}


def compute(calc_type: CalculationType | str, a: float, b: float) -> float:
    return OPERATIONS[CalculationType(calc_type)](a, b)
