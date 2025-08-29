# 🛡️ Heimdall – Multi-Agent Financial Intelligence

Heimdall is a multi-agent orchestration system designed to reason about financial data from multiple perspectives.
It combines specialist supervisors, custom-built tools, and retrieval pipelines to create structured, validated insights — with a human-in-the-loop when needed.

Think of it as an AI research team in a box: one orchestrator delegates missions, supervisors lead domain experts, and writers synthesize everything into a clear, validated report.

🌍 Why Heimdall?

In finance and research, information doesn’t live in one place. It’s scattered across filings, news, markets, and models. A single agent often falls short in reasoning through this complexity.

Heimdall solves this by:

Breaking work into missions with a planner.

Delegating to specialized supervisors (valuation, risk, ESG, etc.).

Synthesizing results through joint report writers.

Validating outputs with both AI and humans before publishing.

This makes it adaptable to domains where accuracy, transparency, and reliability matter.

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

📂 Project Structure
.
├── agents/              # Agent definitions
├── tools/               # Financial, market, valuation, and RAG tools
├── config/              # Configurations (logging, settings)
├── utils/               # Utility helpers
├── data/                # Local dbs, caches (ignored in git)
├── logs/                # Runtime logs (ignored in git)
├── notebooks/           # Prototyping + experiments
├── tests/               # Unit tests
│
├── graph.py             # LangGraph workflow builder
├── state.py             # Global state definitions
├── main.py              # Entry point
├── Dockerfile           # Container setup
├── requirements.txt     # Dependencies
├── README.md            # This file
└── LICENSE

⚙️ Installation
Prerequisites

Python 3.10+

Git

(Optional) Docker

Steps
MacOS / Linux
git clone https://github.com/your-username/heimdall.git
cd heimdall
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Windows (PowerShell)
git clone https://github.com/your-username/heimdall.git
cd heimdall
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

Environment variables

Create a .env file in root:

ALPHAVANTAGE_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key

▶️ Usage

Run locally:

python main.py


Run with Docker:

docker build -t heimdall .
docker run --env-file .env heimdall

🧪 Testing
pytest tests/

🛠️ Tech Stack

Python 3.10+

LangGraph for orchestration

SQLite for local persistence

Docker for containerization

Pytest for testing

🚧 Roadmap

 Add real-time streaming data support

 Improve orchestration with adaptive mission planning

 CI/CD integration with GitHub Actions

 Expand test coverage and logging

📜 License

This project is licensed under the MIT License
.