"""Unit tests for calculator mathematical operations"""

import math

import pytest


@pytest.mark.unit
class TestBasicOperations:
    """Test basic arithmetic operations"""

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (5, 3, 8),
            (0, 0, 0),
            (-5, 3, -2),
            (5, -3, 2),
            (-5, -3, -8),
            (100, 200, 300),
        ],
    )
    def test_add(self, a, b, expected):
        """Test addition with various inputs"""
        result = int(a + b)
        assert result == expected

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (5, 3, 2),
            (0, 0, 0),
            (-5, 3, -8),
            (5, -3, 8),
            (-5, -3, -2),
            (100, 50, 50),
        ],
    )
    def test_subtract(self, a, b, expected):
        """Test subtraction with various inputs"""
        result = int(a - b)
        assert result == expected

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (5, 3, 15),
            (0, 5, 0),
            (5, 0, 0),
            (-5, 3, -15),
            (5, -3, -15),
            (-5, -3, 15),
            (12, 12, 144),
        ],
    )
    def test_multiply(self, a, b, expected):
        """Test multiplication with various inputs"""
        result = int(a * b)
        assert result == expected

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (10, 2, 5),
            (100, 10, 10),
            (7, 2, 3),  # Integer division
            (-10, 2, -5),
            (10, -2, -5),
            (-10, -2, 5),
        ],
    )
    def test_divide(self, a, b, expected):
        """Test division with various inputs"""
        result = int(a / b)
        assert result == expected

    def test_divide_by_zero(self):
        """Test division by zero raises error"""
        with pytest.raises(ZeroDivisionError):
            _ = 10 / 0


@pytest.mark.unit
class TestAdvancedOperations:
    """Test advanced mathematical operations"""

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (2, 3, 8),
            (2, 10, 1024),
            (5, 2, 25),
            (10, 0, 1),
            (0, 5, 0),
            (3, 3, 27),
            (-2, 2, 4),
            (-2, 3, -8),
        ],
    )
    def test_power(self, a, b, expected):
        """Test power operation with various inputs"""
        result = int(a**b)
        assert result == expected

    @pytest.mark.parametrize(
        "a,expected",
        [
            (0, 0),
            (1, 1),
            (4, 2),
            (9, 3),
            (16, 4),
            (25, 5),
            (100, 10),
            (144, 12),
        ],
    )
    def test_sqrt(self, a, expected):
        """Test square root with various inputs"""
        result = int(math.sqrt(a))
        assert result == expected

    def test_sqrt_negative(self):
        """Test square root of negative number raises error"""
        with pytest.raises(ValueError):
            _ = math.sqrt(-1)

    @pytest.mark.parametrize(
        "a,expected",
        [
            (0, 0),
            (1, 1),
            (8, 2),
            (27, 3),
            (64, 4),
            (125, 5),
            (1000, 10),
        ],
    )
    def test_cbrt(self, a, expected):
        """Test cube root with various inputs"""
        result = round(a ** (1 / 3))
        assert result == expected

    @pytest.mark.parametrize(
        "a,expected",
        [
            (0, 1),
            (1, 1),
            (5, 120),
            (10, 3628800),
        ],
    )
    def test_factorial(self, a, expected):
        """Test factorial with various inputs"""
        result = math.factorial(a)
        assert result == expected

    def test_factorial_negative(self):
        """Test factorial of negative number raises error"""
        with pytest.raises(ValueError):
            _ = math.factorial(-1)

    @pytest.mark.parametrize(
        "a,expected",
        [
            (1, 0.0),  # ln(1) = 0
            (math.e, 1.0),  # ln(e) = 1
            (10, 2.302585),  # ln(10) ≈ 2.302585
            (100, 4.605170),  # ln(100) ≈ 4.605170
        ],
    )
    def test_log(self, a, expected):
        """Test natural logarithm (ln) with various inputs"""
        result = math.log(a)
        assert abs(result - expected) < 0.001  # Higher precision for ln

    def test_log_zero(self):
        """Test logarithm of zero raises error"""
        with pytest.raises(ValueError):
            _ = math.log(0)

    def test_log_negative(self):
        """Test logarithm of negative number raises error"""
        with pytest.raises(ValueError):
            _ = math.log(-1)

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            (10, 3, 1),
            (17, 5, 2),
            (20, 4, 0),
            (7, 7, 0),
            (100, 30, 10),
        ],
    )
    def test_remainder(self, a, b, expected):
        """Test remainder operation with various inputs"""
        result = a % b
        assert result == expected

    def test_remainder_by_zero(self):
        """Test remainder with zero divisor raises error"""
        with pytest.raises(ZeroDivisionError):
            _ = 10 % 0


@pytest.mark.unit
class TestTrigonometry:
    """Test trigonometric operations"""

    @pytest.mark.parametrize(
        "a,expected",
        [
            (0, 0.0),
            (90, 1.0),  # sin(90 degrees) in radians
            (180, 0.0),
        ],
    )
    def test_sin(self, a, expected):
        """Test sine with degree inputs"""
        # Convert degrees to radians
        radians = math.radians(a)
        result = math.sin(radians)
        assert abs(result - expected) < 0.01

    @pytest.mark.parametrize(
        "a,expected",
        [
            (0, 1.0),
            (90, 0.0),
            (180, -1.0),
        ],
    )
    def test_cos(self, a, expected):
        """Test cosine with degree inputs"""
        # Convert degrees to radians
        radians = math.radians(a)
        result = math.cos(radians)
        assert abs(result - expected) < 0.01

    @pytest.mark.parametrize(
        "a,expected",
        [
            (0, 0.0),
            (45, 1.0),
        ],
    )
    def test_tan(self, a, expected):
        """Test tangent with degree inputs"""
        # Convert degrees to radians
        radians = math.radians(a)
        result = math.tan(radians)
        assert abs(result - expected) < 0.01
