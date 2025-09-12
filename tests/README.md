# Heimdall Test Suite Documentation

## Overview

This document provides comprehensive guidance for the Heimdall test suite, including best practices, test structure, and maintenance guidelines.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_config.py           # Configuration and settings tests
├── test_data_providers.py   # Data provider integration tests
├── test_graph_workflow.py   # LangGraph workflow tests
├── test_agents.py           # Agent functionality tests
├── test_tools.py            # Tool integration tests
├── test_edge_cases.py       # Edge cases and boundary conditions
└── README.md               # This documentation
```

## Test Categories

### 1. Unit Tests
- **Purpose**: Test individual functions and classes in isolation
- **Markers**: `@pytest.mark.unit`
- **Examples**: Input validation, data transformation, utility functions

### 2. Integration Tests
- **Purpose**: Test interactions between components
- **Markers**: `@pytest.mark.integration`
- **Examples**: API integrations, database operations, workflow coordination

### 3. Async Tests
- **Purpose**: Test asynchronous functionality
- **Markers**: `@pytest.mark.asyncio`
- **Examples**: API calls, concurrent operations, async workflows

### 4. Slow Tests
- **Purpose**: Tests that take significant time to run
- **Markers**: `@pytest.mark.slow`
- **Examples**: Full workflow tests, large dataset processing

## Running Tests

### Basic Test Execution
```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_config.py

# Run specific test class
python -m pytest tests/test_config.py::TestAPIKeyValidation

# Run specific test method
python -m pytest tests/test_config.py::TestAPIKeyValidation::test_validate_api_keys_success
```

### Test Filtering
```bash
# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Skip slow tests
python -m pytest -m "not slow"

# Run async tests only
python -m pytest -m asyncio
```

### Coverage Reports
```bash
# Run tests with coverage
python -m pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Best Practices

### 1. Test Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names that explain what is being tested

### 2. Test Structure (AAA Pattern)
```python
def test_function_name(self) -> None:
    """Test description explaining what is being tested."""
    # Arrange - Set up test data and conditions
    input_data = "test_input"
    expected_result = "expected_output"
    
    # Act - Execute the function being tested
    result = function_under_test(input_data)
    
    # Assert - Verify the results
    assert result == expected_result
```

### 3. Fixture Usage
```python
# Use fixtures for common test data
def test_with_fixture(self, sample_financial_data: Dict[str, Any]) -> None:
    """Test using shared fixture data."""
    assert "ticker" in sample_financial_data
    assert sample_financial_data["ticker"] == "AAPL"
```

### 4. Mocking External Dependencies
```python
@patch('src.tools.data_providers.financial_modeling_prep._make_fmp_request')
async def test_api_call(self, mock_request: AsyncMock) -> None:
    """Test API call with mocked external dependency."""
    mock_request.return_value = {"status": "success"}
    
    result = await get_financial_data("AAPL")
    
    assert result["status"] == "success"
    mock_request.assert_called_once()
```

### 5. Exception Testing
```python
def test_invalid_input_raises_exception(self) -> None:
    """Test that invalid input raises appropriate exception."""
    with pytest.raises(ValueError) as exc_info:
        validate_ticker("")
    
    assert "Ticker cannot be empty" in str(exc_info.value)
```

### 6. Parametrized Tests
```python
@pytest.mark.parametrize("input_value,expected", [
    ("AAPL", "AAPL"),
    ("msft", "MSFT"),
    (" GOOGL ", "GOOGL"),
])
def test_ticker_normalization(self, input_value: str, expected: str) -> None:
    """Test ticker normalization with various inputs."""
    result = normalize_ticker(input_value)
    assert result == expected
```

## Common Test Patterns

### 1. API Testing Pattern
```python
@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_api_success(self, mock_get: AsyncMock) -> None:
    """Test successful API response."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value.__aenter__.return_value = mock_response
    
    result = await api_function()
    
    assert result["data"] == "test"
```

### 2. Error Handling Pattern
```python
@pytest.mark.asyncio
async def test_api_error_handling(self) -> None:
    """Test API error handling."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = Exception("Network error")
        
        result = await api_function()
        
        assert "error" in result
        assert "Network error" in result["error"]
```

### 3. State Testing Pattern
```python
def test_state_management(self) -> None:
    """Test state updates and persistence."""
    state = HeimdallState(ticker="AAPL", company_name="Apple Inc.", messages=[])
    
    # Test initial state
    assert state["ticker"] == "AAPL"
    
    # Test state updates
    state["financial_report"] = "Test report"
    assert state["financial_report"] == "Test report"
```

## Debugging Tests

### 1. Using pytest debugging
```bash
# Drop into debugger on failure
python -m pytest --pdb

# Drop into debugger on first failure
python -m pytest -x --pdb
```

### 2. Verbose output
```bash
# Show print statements
python -m pytest -s

# Show detailed assertion information
python -m pytest -vvv
```

### 3. Test isolation
```bash
# Run single test in isolation
python -m pytest tests/test_config.py::test_specific_function -v
```

## Maintenance Guidelines

### 1. Regular Test Review
- Review tests monthly for relevance and accuracy
- Update tests when functionality changes
- Remove obsolete tests

### 2. Performance Monitoring
- Monitor test execution time
- Optimize slow tests or mark them appropriately
- Use fixtures to reduce setup time

### 3. Coverage Monitoring
- Maintain >80% code coverage
- Focus on critical business logic
- Don't chase 100% coverage at the expense of test quality

### 4. Test Data Management
- Keep test data minimal and focused
- Use factories for complex test data
- Clean up test data after tests complete

## Continuous Integration

### 1. Pre-commit Hooks
Tests are automatically run via pre-commit hooks:
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### 2. GitHub Actions
Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled nightly runs

### 3. Test Requirements
- All tests must pass before merging
- New features require corresponding tests
- Bug fixes should include regression tests

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure PYTHONPATH includes src directory
   - Check for circular imports
   - Verify all dependencies are installed

2. **Async Test Issues**
   - Use `@pytest.mark.asyncio` for async tests
   - Ensure proper event loop handling
   - Mock async dependencies correctly

3. **Fixture Issues**
   - Check fixture scope (function, class, module, session)
   - Ensure fixtures are properly imported
   - Verify fixture dependencies

4. **Mock Issues**
   - Patch at the correct level
   - Use proper mock types (Mock vs AsyncMock)
   - Reset mocks between tests

### Getting Help

- Check pytest documentation: https://docs.pytest.org/
- Review existing tests for patterns
- Ask team members for guidance
- Use pytest plugins for additional functionality

## Contributing

When adding new tests:

1. Follow the established patterns and conventions
2. Include proper docstrings and type hints
3. Add appropriate markers for test categorization
4. Update this documentation if needed
5. Ensure tests are deterministic and isolated

Remember: Good tests are an investment in code quality and team productivity!
