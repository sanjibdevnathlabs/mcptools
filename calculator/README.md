# Calculator MCP Server

A simple and fast Model Context Protocol (MCP) server providing basic and advanced mathematical operations.

## 🚀 Features

- **Basic Operations**: Addition, subtraction, multiplication, division
- **Advanced Operations**: Power, square root, logarithm, trigonometry
- **TOML Configuration**: Modern configuration system
- **Multi-Transport**: stdio, SSE, and streamable-http support
- **Zero Dependencies**: Pure Python math operations
- **Fast**: Minimal overhead for quick calculations

## 📦 Installation

### Prerequisites
- Python 3.11+ (3.10+ with `tomli`)
- Virtual environment (recommended)

### Quick Setup

```bash
# From project root
cd /path/to/mcptools

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the server
python -m calculator
```

## ⚙️ Configuration

### TOML Configuration Files

**`calculator/environment/default.toml`** (Base configuration)
```toml
[app]
# Application configuration
name = "calculator-mcp-server"

[server]
# Server configuration
transport_mode = "stdio"  # Options: stdio, sse, streamable-http
```

**`calculator/environment/dev.toml`** (Development overrides - gitignored)
```toml
# Currently using all defaults from default.toml
# Add development-specific overrides here if needed
```

## 🚦 Usage

### Starting the Server

```bash
# Default (uses stdio from default.toml)
python -m calculator

# The transport mode is configured in TOML files
# Edit calculator/environment/dev.toml to change transport
```

### Testing with MCP Inspector

**STDIO Mode:**
```bash
# In MCP Inspector:
Transport: STDIO
Command: /absolute/path/to/mcptools/venv/bin/python
Arguments: -m calculator
Working Directory: /absolute/path/to/mcptools
```

**SSE Mode:**
```bash
# Set transport in dev.toml:
# [server]
# transport_mode = "sse"

python -m calculator

# In MCP Inspector:
Transport: SSE
URL: http://localhost:5000/sse
```

**HTTP Mode:**
```bash
# Set transport in dev.toml:
# [server]
# transport_mode = "streamable-http"

python -m calculator

# In MCP Inspector:
Transport: HTTP
URL: http://localhost:5000
```

## 📖 API Reference

### Available Tools

#### Basic Operations

##### `add`
Add two numbers.

```python
# Parameters:
a: int  # First number
b: int  # Second number

# Returns:
int  # Sum of a and b

# Example:
add(a=5, b=3)  # Returns: 8
```

##### `subtract`
Subtract two numbers.

```python
# Parameters:
a: int  # First number
b: int  # Second number

# Returns:
int  # Difference (a - b)

# Example:
subtract(a=10, b=4)  # Returns: 6
```

##### `multiply`
Multiply two numbers.

```python
# Parameters:
a: int  # First number
b: int  # Second number

# Returns:
int  # Product of a and b

# Example:
multiply(a=7, b=6)  # Returns: 42
```

##### `divide`
Divide two numbers.

```python
# Parameters:
a: float  # Numerator
b: float  # Denominator

# Returns:
float  # Quotient (a / b)

# Raises:
ValueError  # If b is zero

# Example:
divide(a=10.0, b=2.0)  # Returns: 5.0
```

#### Advanced Operations

##### `power`
Raise a number to a power.

```python
# Parameters:
base: float     # Base number
exponent: float # Exponent

# Returns:
float  # base raised to exponent

# Example:
power(base=2.0, exponent=3.0)  # Returns: 8.0
```

##### `sqrt`
Calculate square root.

```python
# Parameters:
number: float  # Number to find square root of

# Returns:
float  # Square root

# Raises:
ValueError  # If number is negative

# Example:
sqrt(number=16.0)  # Returns: 4.0
```

##### `log`
Calculate natural logarithm.

```python
# Parameters:
number: float  # Number to find logarithm of

# Returns:
float  # Natural logarithm (base e)

# Raises:
ValueError  # If number <= 0

# Example:
log(number=2.718281828)  # Returns: ~1.0
```

##### `log10`
Calculate base-10 logarithm.

```python
# Parameters:
number: float  # Number to find logarithm of

# Returns:
float  # Base-10 logarithm

# Raises:
ValueError  # If number <= 0

# Example:
log10(number=100.0)  # Returns: 2.0
```

#### Trigonometric Operations

##### `sin`
Calculate sine (in radians).

```python
# Parameters:
angle: float  # Angle in radians

# Returns:
float  # Sine of angle

# Example:
sin(angle=1.5708)  # Returns: ~1.0 (π/2 radians = 90°)
```

##### `cos`
Calculate cosine (in radians).

```python
# Parameters:
angle: float  # Angle in radians

# Returns:
float  # Cosine of angle

# Example:
cos(angle=3.14159)  # Returns: ~-1.0 (π radians = 180°)
```

##### `tan`
Calculate tangent (in radians).

```python
# Parameters:
angle: float  # Angle in radians

# Returns:
float  # Tangent of angle

# Example:
tan(angle=0.7854)  # Returns: ~1.0 (π/4 radians = 45°)
```

## 💡 Examples

### Basic Calculations

```python
# Simple arithmetic
add(a=10, b=5)        # 15
subtract(a=10, b=5)   # 5
multiply(a=10, b=5)   # 50
divide(a=10.0, b=5.0) # 2.0

# Complex expressions
power(base=2.0, exponent=10.0)  # 1024.0
sqrt(number=144.0)               # 12.0
```

### Scientific Calculations

```python
# Logarithms
log(number=2.718281828)   # 1.0 (natural log of e)
log10(number=1000.0)      # 3.0 (10^3 = 1000)

# Trigonometry (angles in radians)
sin(angle=1.5708)   # 1.0 (90° in radians)
cos(angle=0.0)      # 1.0 (0°)
tan(angle=0.7854)   # 1.0 (45° in radians)
```

### Chained Operations

Use MCP Inspector to chain operations:

```
1. Calculate: power(base=2.0, exponent=4.0)     → 16.0
2. Calculate: sqrt(number=16.0)                  → 4.0
3. Calculate: multiply(a=4, b=3)                 → 12
4. Calculate: divide(a=12.0, b=4.0)              → 3.0
```

## 🔧 Development

### Configuration Structure

```python
from calculator.config import Config

# Initialize config
config = Config()

# Access configuration
print(config.app.name)              # "calculator-mcp-server"
print(config.server.transport_mode) # "stdio"
```

### Adding New Operations

1. Add new tool in `calculator/main.py`:

```python
@mcp.tool()
def factorial(n: int) -> int:
    """Calculate factorial of n"""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
```

2. Test with MCP Inspector
3. Update README with documentation

## 🐛 Troubleshooting

### Division by Zero

```python
# ❌ This will raise an error
divide(a=10.0, b=0.0)  # ValueError: Cannot divide by zero

# ✅ Always check denominator
if b != 0:
    divide(a=10.0, b=b)
```

### Negative Square Roots

```python
# ❌ This will raise an error
sqrt(number=-4.0)  # ValueError: Cannot calculate square root of negative number

# ✅ Use absolute value if needed
sqrt(number=abs(-4.0))  # 2.0
```

### Logarithm of Non-Positive Numbers

```python
# ❌ These will raise errors
log(number=0.0)   # ValueError
log(number=-1.0)  # ValueError

# ✅ Always use positive numbers
log(number=1.0)   # 0.0
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add new operations in `calculator/main.py`
4. Test with MCP Inspector
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Built with FastMCP for fast mathematical operations via Model Context Protocol.**

