# Contributing to AWS Financial Data Mesh

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, AWS region, etc.)

### Suggesting Features

Feature requests are welcome! Please create an issue describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/aws-financial-data-mesh.git
   cd aws-financial-data-mesh
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, readable code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Run tests
   pytest
   
   # Check code quality
   black src/
   flake8 src/
   mypy src/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Describe your changes

## Code Style

- **Python**: Follow PEP 8
- **Formatting**: Use `black` for code formatting
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings
- **Imports**: Organize imports with `isort`

Example:
```python
def process_trade(
    trade_id: str,
    quantity: int,
    price: Decimal
) -> Dict[str, Any]:
    """
    Process a trade event.
    
    Args:
        trade_id: Unique trade identifier
        quantity: Number of shares
        price: Execution price
        
    Returns:
        Processed trade data
        
    Raises:
        ValueError: If trade_id is invalid
    """
    # Implementation
    pass
```

## Testing

- Write unit tests for all new functionality
- Maintain test coverage above 80%
- Use pytest for testing
- Mock AWS services with moto

Example test:
```python
def test_trade_publisher():
    """Test trade event publishing."""
    publisher = TradeEventPublisher()
    
    trade = {
        'trade_id': 'TRD0000001234',
        'instrument': 'AAPL',
        'quantity': 100,
        'price': Decimal('150.25'),
        'trader_id': 'TRD001',
        'direction': 'BUY',
        'exchange': 'NASDAQ'
    }
    
    event_id = publisher.publish_trade(trade)
    assert event_id is not None
```

## Documentation

- Update README.md for significant changes
- Add docstrings to all functions and classes
- Update architecture diagrams if needed
- Add examples for new features

## Code Review Process

All submissions require review. We use GitHub pull requests for this purpose.

- Maintainers will review your PR
- Address any feedback
- Once approved, your PR will be merged

## Community

- Be respectful and constructive
- Help others in discussions
- Share your use cases and experiences

## Questions?

- Open an issue for questions
- Reach out on LinkedIn: [Agnibes Banerjee](https://linkedin.com/in/agnibeshbanerjee)

Thank you for contributing! 🙏
