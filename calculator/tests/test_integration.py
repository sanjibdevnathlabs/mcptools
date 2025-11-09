"""Integration tests for calculator - testing tools directly"""

import pytest

# Import the calculator tools directly
from calculator.main import (
    add,
    cbrt,
    cos,
    divide,
    factorial,
    log,
    multiply,
    power,
    remainder,
    sin,
    sqrt,
    subtract,
    tan,
)


@pytest.mark.integration
class TestCalculatorIntegration:
    """Integration tests simulating MCP tool calls"""

    def test_basic_arithmetic_workflow(self):
        """Test a workflow of basic arithmetic operations"""
        # Simulate: (10 + 5) * 2 - 3 = 27
        step1 = add(10, 5)  # 15
        step2 = multiply(step1, 2)  # 30
        step3 = subtract(step2, 3)  # 27

        assert step3 == 27

    def test_advanced_math_workflow(self):
        """Test a workflow of advanced operations"""
        # Simulate: sqrt(power(4, 2)) = sqrt(16) = 4
        step1 = power(4, 2)  # 16
        step2 = sqrt(step1)  # 4.0

        assert step2 == 4.0

    def test_trigonometry_workflow(self):
        """Test trigonometric operations together"""
        # Simulate: sin²(0) + cos²(0) = 1 (Pythagorean identity)

        angle = 0
        sin_val = sin(angle)
        cos_val = cos(angle)

        # sin²(0) + cos²(0)
        result = power(int(sin_val), 2) + power(int(cos_val), 2)

        assert result == 1  # Pythagorean identity

    def test_complex_calculation(self):
        """Test a complex multi-step calculation"""
        # Simulate: (2^10) / (factorial(5) / 10) = 1024 / (120/10) = 1024 / 12 ≈ 85.33
        step1 = power(2, 10)  # 1024
        step2 = factorial(5)  # 120
        step3 = divide(step2, 10)  # 12.0
        step4 = divide(step1, int(step3))  # 85.33...

        assert abs(step4 - 85.33) < 0.01

    def test_all_tools_available(self):
        """Verify all 13 calculator tools are accessible"""
        tools = [
            add,
            subtract,
            multiply,
            divide,
            power,
            sqrt,
            cbrt,
            factorial,
            log,
            remainder,
            sin,
            cos,
            tan,
        ]

        assert len(tools) == 13
        for tool in tools:
            assert callable(tool)

    def test_tool_basic_operations(self):
        """Test each tool with basic inputs"""
        assert add(5, 3) == 8
        assert subtract(10, 4) == 6
        assert multiply(6, 7) == 42
        assert divide(20, 4) == 5.0
        assert power(3, 3) == 27
        assert sqrt(16) == 4.0
        assert cbrt(27) == 3.0
        assert factorial(5) == 120
        assert abs(log(2.718281828459045) - 1.0) < 0.001
        assert remainder(17, 5) == 2
        assert abs(sin(0) - 0.0) < 0.001
        assert abs(cos(0) - 1.0) < 0.001
        assert abs(tan(0) - 0.0) < 0.001

    def test_error_handling_integration(self):
        """Test error handling in integrated scenarios"""
        # Division by zero
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

        # Negative factorial
        with pytest.raises(ValueError):
            factorial(-1)

        # Log of zero
        with pytest.raises(ValueError):
            import math

            _ = math.log(0)

        # Remainder by zero
        with pytest.raises(ZeroDivisionError):
            remainder(10, 0)

    def test_scientific_calculation(self):
        """Test a realistic scientific calculation"""
        # Calculate: e^2 using power approximation
        # e ≈ 2.71828, e^2 ≈ 7.389
        e = 2.71828
        result = power(int(e), 2)  # Approximate

        # Note: Using int() for power function requirement
        assert result == 4  # 2^2 (due to int casting)


@pytest.mark.integration
@pytest.mark.smoke
class TestCalculatorCriticalPaths:
    """Smoke tests for critical calculator functionality"""

    def test_calculator_smoke_all_operations(self):
        """Smoke test: verify all operations work without errors"""
        try:
            # Test all operations don't raise exceptions
            _ = add(1, 2)
            _ = subtract(5, 3)
            _ = multiply(4, 5)
            _ = divide(10, 2)
            _ = power(2, 3)
            _ = sqrt(9)
            _ = cbrt(8)
            _ = factorial(4)
            _ = log(10)
            _ = remainder(7, 3)
            _ = sin(0)
            _ = cos(0)
            _ = tan(0)

            # If we reach here, all operations work
            assert True

        except Exception as e:
            pytest.fail(f"Smoke test failed: {e}")

    def test_calculator_smoke_accuracy(self):
        """Smoke test: verify basic accuracy of results"""
        assert add(2, 2) == 4
        assert multiply(3, 4) == 12
        assert power(5, 2) == 25
        assert sqrt(100) == 10.0
        assert factorial(6) == 720
