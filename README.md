# 🛡️ Heimdall – Multi-Agent Financial Intelligence System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

Heimdall is an enterprise-grade, multi-agent orchestration system that delivers comprehensive financial analysis through specialized AI agents. Built on LangGraph and LangChain, it provides institutional-quality research reports by coordinating domain experts across valuation, risk assessment, compliance, and market analysis.

Heimdall is a world-class, autonomous intelligence platform architected to function as a force multiplier for financial analysis teams. Its purpose is to automate the entire financial intelligence lifecycle—from dynamic mission planning and deep data analysis to the creation of compliant, internally-defended, and human-refined strategic reports.
The role of Heimdall Version 1 is to serve as The Autonomous Analyst. It transforms a single company name into a comprehensive, institutional-grade intelligence report with unprecedented speed and analytical rigor. It achieves this by leveraging a hierarchical consortium of specialized AI agents, orchestrated through a stateful, resilient workflow that emphasizes defensibility, compliance, and collaboration, as defined in the project's src architecture.

## 🎯 Key Features

- **Multi-Agent Architecture**: Hierarchical system with specialized supervisors and domain experts
- **Comprehensive Analysis**: Financial statements, valuations (DCF, Comps), risk assessment, and compliance checking
- **Real-time Data Integration**: 15+ financial data providers including Bloomberg-equivalent APIs
- **Regulatory Compliance**: Built-in SEC, SEBI, and CFA compliance checking with structured reporting
- **Professional Output**: Automated PDF report generation with institutional formatting
- **Validation Pipeline**: Multi-layer validation with AI and human-in-the-loop capabilities
- **Production Ready**: Full logging, monitoring, error handling, and deployment infrastructure

## 🏗️ Architecture Overview

Heimdall implements a sophisticated multi-agent system inspired by professional financial research teams:

🧠 System Flow
[ Orchestrator ]
        |
        v
[ Mission Planner Agent ]
        |
        v
[ Main Supervisor ]
        |
        v
+-----------------------------------+
| 5 Domain Supervisors              |
| - ESG Analyst Supervisor          |
| - Valuation Supervisor            |
| - Risk Research Supervisor        |
| - Competitive Analysis Supervisor |
| - Industry Analysis Supervisor    |
+-----------------------------------+
        |
        v
[ Joint Report Writer ]
        |
        v
[ Validation Supervisor ]
        |
        v
[ Human-in-the-Loop (optional) ]
       | \
       |  \
       |   -> If issues -> back to Joint Report Writer
        v
[ Final Report Writer ]

## 📊 Data Sources & APIs

Heimdall integrates with 15+ professional financial data providers:

- **Market Data**: Alpha Vantage, Polygon.io, Finnhub
- **Financial Statements**: Financial Modeling Prep, SEC EDGAR
- **Economic Data**: Federal Reserve Economic Data (FRED)
- **News & Sentiment**: Tavily Search, Financial news APIs
- **Regulatory**: SEC filings, SEBI data, CFA standards

## 📂 Project Structure

```
heimdall/
├── src/
│   ├── agents/              # Multi-agent system components
│   │   ├── domain/          # Specialized domain agents
│   │   ├── supervisors/     # Hierarchical supervisors
│   │   └── validation/      # Quality assurance agents
│   ├── tools/               # Financial data tools & APIs
│   │   ├── data_providers/  # External API integrations
│   │   ├── analysis/        # Technical & fundamental analysis
│   │   └── compliance/      # Regulatory compliance tools
│   ├── graph/               # LangGraph workflow definitions
│   ├── config/              # Configuration & logging
│   └── prompts/             # Agent prompts & templates
├── tests/                   # Comprehensive test suite
├── docs/                    # Documentation
├── requirements.txt         # Production dependencies
├── pyproject.toml          # Project configuration
└── Makefile                # Development commands
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Git
- API keys for financial data providers

### Installation

```bash
# Clone repository
git clone https://github.com/divyyadav/heimdall.git
cd heimdall

# Set up development environment
make setup-dev

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Copy `.env.example` to `.env` and configure your API keys:

```bash
# Primary Language Model (Required)
google="your_gemini_api_key"

# Financial Data Providers (Required)
FPREP="your_fmp_api_key"
FINNHUB_API_KEY="your_finnhub_key"
Alpha_Vantage_Stock_API="your_av_key"
polygon_api="your_polygon_key"

# Additional APIs (see .env.example for complete list)
```

### Usage

```bash
# Run analysis
python -m src.main_flow.main

# Run with Docker
make docker-build
make docker-run

# Development commands
make format          # Format code
make lint           # Run linting
make test           # Run tests
make test-coverage  # Run tests with coverage
```

## 🧪 Testing & Quality Assurance

Heimdall maintains high code quality standards:

```bash
# Run full test suite
make test

# Run with coverage report
make test-coverage

# Code quality checks
make lint
make type-check
make security-check

# Format code
make format
```

## 🛠️ Technology Stack

- **Core Framework**: Python 3.10+, LangChain, LangGraph
- **AI/ML**: Google Gemini, OpenAI GPT models
- **Data Storage**: ChromaDB (vector), SQLite (relational)
- **APIs**: 15+ financial data providers
- **Testing**: Pytest, Coverage.py
- **Code Quality**: Black, isort, flake8, mypy, bandit
- **Deployment**: Docker, GitHub Actions

## 🏢 Enterprise Features

- **Compliance**: Built-in SEC, SEBI, CFA regulatory checking
- **Audit Trail**: Comprehensive logging and monitoring
- **Scalability**: Async processing and connection pooling
- **Security**: API key management, data encryption
- **Validation**: Multi-layer quality assurance pipeline

## 📈 Performance

- **Concurrent Processing**: Multiple agents work in parallel
- **Caching**: Intelligent data caching to reduce API calls
- **Rate Limiting**: Respectful API usage with backoff strategies
- **Memory Optimization**: Efficient data structures and streaming

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes following our coding standards
4. Add tests and documentation
5. Submit a pull request

## 📚 Documentation

- [Contributing Guidelines](CONTRIBUTING.md)
- [API Documentation](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)

## 🚧 Roadmap

- [ ] Real-time streaming data integration
- [ ] Advanced portfolio optimization models
- [ ] Multi-language support
- [ ] Web-based dashboard
- [ ] Mobile API endpoints
- [ ] Advanced compliance automation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with ❤️ using:
- [LangChain](https://langchain.com/) - AI application framework
- [LangGraph](https://langgraph-doc.vercel.app/) - Multi-agent orchestration
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Pydantic](https://pydantic.dev/) - Data validation