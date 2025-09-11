# Contributing to Heimdall Financial Intelligence System

Thank you for your interest in contributing to Heimdall! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Git
- Docker (optional)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/divyyadav/heimdall.git
cd heimdall

# Set up development environment
make setup-dev

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys
```

## Development Workflow

### Code Style
We use strict code formatting and quality standards:

- **Black** for code formatting (120 character line length)
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **bandit** for security analysis

Run all formatting and checks:
```bash
make format
make lint
make type-check
make security-check
```

### Pre-commit Hooks
Install pre-commit hooks to automatically run checks:
```bash
make pre-commit
```

### Testing
Write comprehensive tests for all new functionality:

```bash
# Run tests
make test

# Run with coverage
make test-coverage
```

Test files should be placed in the `tests/` directory and follow the naming convention `test_*.py`.

## Architecture Guidelines

### Multi-Agent System Design
Heimdall follows a hierarchical multi-agent architecture:

1. **Orchestrator Agent** - Top-level coordination
2. **Main Supervisor** - Delegates to domain supervisors
3. **Domain Supervisors** - Manage specialized agents
4. **Specialist Agents** - Perform specific analysis tasks

### Code Organization
```
src/
├── agents/          # Agent implementations
├── config/          # Configuration management
├── graph/           # LangGraph workflow definitions
├── tools/           # Financial data tools and APIs
├── prompts/         # Agent prompts and templates
└── model_schemas/   # Pydantic data models
```

### Data Flow
1. **Input Processing** - Ticker symbol and analysis requirements
2. **Mission Planning** - High-level analysis strategy
3. **Parallel Analysis** - Multiple domain experts work simultaneously
4. **Report Synthesis** - Combine insights into unified report
5. **Validation** - Quality assurance and fact-checking
6. **Output Generation** - Professional PDF reports

## API Integration Standards

### Error Handling
All API integrations must include:
- Comprehensive error handling
- Rate limiting respect
- Retry logic with exponential backoff
- Proper logging

### Data Validation
Use Pydantic models for all data structures:
```python
from pydantic import BaseModel, Field
from typing import Optional

class FinancialMetrics(BaseModel):
    revenue: float = Field(..., description="Total revenue")
    net_income: Optional[float] = Field(None, description="Net income")
```

### Async Operations
All API calls should be asynchronous:
```python
import aiohttp
from typing import Dict, Any

async def fetch_data(ticker: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        # Implementation
        pass
```

## Contribution Types

### Bug Reports
When reporting bugs, include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Relevant logs or error messages

### Feature Requests
For new features, provide:
- Clear use case description
- Proposed implementation approach
- Impact on existing functionality
- Any breaking changes

### Code Contributions
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes following the guidelines above
4. Add tests for new functionality
5. Ensure all checks pass: `make pre-commit`
6. Submit a pull request

### Documentation
Documentation improvements are always welcome:
- Code comments and docstrings
- README updates
- Architecture documentation
- API documentation

## Pull Request Process

1. **Title**: Use descriptive titles (e.g., "Add DCF valuation model", "Fix API rate limiting")
2. **Description**: Explain what changes were made and why
3. **Testing**: Ensure all tests pass and add new tests if needed
4. **Documentation**: Update relevant documentation
5. **Review**: Address feedback from maintainers

### PR Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Security considerations addressed

## Financial Data Compliance

### Regulatory Considerations
- Ensure all data usage complies with provider terms of service
- Implement proper data attribution
- Respect rate limits and usage quotas
- Handle sensitive financial data appropriately

### Data Quality
- Validate all financial data inputs
- Implement data freshness checks
- Handle missing or incomplete data gracefully
- Log data quality issues for monitoring

## Performance Guidelines

### Async Best Practices
- Use `asyncio` for I/O bound operations
- Implement proper connection pooling
- Handle concurrent request limits
- Use caching where appropriate

### Memory Management
- Stream large datasets when possible
- Implement pagination for large result sets
- Clean up resources properly
- Monitor memory usage in long-running processes

## Security Guidelines

### API Key Management
- Never commit API keys to version control
- Use environment variables for configuration
- Implement key rotation procedures
- Monitor API usage for anomalies

### Data Protection
- Encrypt sensitive data at rest
- Use HTTPS for all external communications
- Implement proper access controls
- Log security-relevant events

## Getting Help

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Documentation**: Check the README and inline documentation
- **Code Review**: Maintainers will provide feedback on pull requests

## Recognition

Contributors will be acknowledged in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- Project documentation

Thank you for helping make Heimdall better!
