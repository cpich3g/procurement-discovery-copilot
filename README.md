# Procurement Discovery Tool

An AI-powered procurement discovery tool built with LangChain and LangGraph that automates vendor and partner discovery for procurement teams using Azure OpenAI.

## 🚀 Features

- **AI-Powered Service Clarification**: Automatically clarifies and enriches procurement requests
- **Comprehensive Service Descriptions**: Generates detailed technical specifications and requirements
- **Global Vendor Discovery**: Identifies and ranks leading vendors using web search
- **Regional Partner Identification**: Finds local partners and distributors
- **Price Benchmarking**: Provides realistic market pricing analysis
- **Multi-Format Reports**: Generates reports in JSON, HTML, and Markdown formats
- **Azure OpenAI Integration**: Full Azure OpenAI support with intelligent model selection
- **Reasoning Model Support**: Uses o3/o3-mini models for complex analysis tasks

## 🏗️ Architecture

The system uses a multi-agent architecture built on LangGraph:

- **Orchestrator Agent**: Manages workflow coordination and state transitions
- **Clarification Agent**: Validates and enriches input requirements (GPT-4.1)
- **Description Agent**: Generates comprehensive service descriptions (o3/o3-mini)
- **Search Agent**: Discovers vendors and partners using Tavily search (o3/o3-mini)
- **Report Generation Agent**: Compiles comprehensive procurement reports (o3/o3-mini)

### 🧠 Intelligent Model Selection

The system automatically selects the best model for each task:
- **Standard Tasks**: GPT-4.1 for input validation and basic processing
- **Analysis Tasks**: o3/o3-mini for complex reasoning and analysis
- **Search Tasks**: o3/o3-mini for sophisticated search result interpretation

## ⚡ Quick Start

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- Azure OpenAI resource with deployed models:
  - GPT-4 (deployment name: `gpt-4.1`) for standard tasks
  - o3-mini (deployment name: `o3`) for reasoning tasks
- Tavily API key (for web search)

### Installation

1. Install uv (if not already installed):
```bash
# On Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone https://github.com/cpich3g/procurement-discovery-copilot.git
cd procurement-discovery-copilot
```

3. Create virtual environment and install dependencies:
```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

# Install dependencies
uv sync
```

4. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials (see Configuration section below)
```

### Alternative Installation (using pip)

If you prefer using pip:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with the following settings:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Model Deployment Names in Azure OpenAI
LLM_MODEL=gpt-4.1
REASONING_MODEL=o3

# Search Configuration
TAVILY_API_KEY=your_tavily_api_key

# Optional Settings
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=20000
REASONING_MAX_COMPLETION_TOKENS=40000
USE_REASONING_MODEL_FOR_ANALYSIS=true
USE_REASONING_MODEL_FOR_COMPLEX_SEARCH=true
```

## 🎯 Usage

### Command Line Interface

Basic usage:
```bash
# Using uv (recommended)
uv run python -m src.main "Cloud Storage" "United States"

# Or with activated virtual environment
python -m src.main "Cloud Storage" "United States"
```

With additional details:
```bash
uv run python -m src.main "ERP Software" "Germany" --details "Manufacturing company with 500 employees"
```

Save results to different formats:
```bash
# JSON format (default)
uv run python -m src.main "Marketing Automation" "Canada" --output results.json

# HTML report with professional styling
uv run python -m src.main "CRM Software" "UK" --output report.html

# Markdown documentation
uv run python -m src.main "Video Conferencing" "Australia" --output summary.md
```

### Python API

```python
from src.main import ProcurementDiscoveryApp

app = ProcurementDiscoveryApp()

# Synchronous usage
results = app.discover(
    service_name="Enterprise CRM Software",
    country="Germany",
    additional_details="Manufacturing company with 500 employees"
)

# Save to file
app.discover(
    service_name="Cloud Storage", 
    country="United States",
    output_file="cloud_storage_report.html"
)

print(results)
```

### Async Usage

```python
import asyncio
from src.main import ProcurementDiscoveryApp

async def main():
    app = ProcurementDiscoveryApp()
    
    results = await app.adiscover(
        service_name="CRM Software", 
        country="United Kingdom",
        additional_details="Enterprise-grade with GDPR compliance"
    )
    
    return results

results = asyncio.run(main())
```

## � Output Format

The tool generates comprehensive reports including:

### Executive Summary
- High-level overview and key recommendations
- Strategic implications and business case
- Cost analysis and vendor comparison

### Service Analysis
- Detailed technical specifications
- Key features and requirements
- Technical architecture and compliance needs

### Vendor Rankings
- Scored vendor comparison (out of 100)
- Detailed vendor profiles with strengths/weaknesses
- Fit assessment for specific requirements
- Contact and pricing information

### Partner Recommendations  
- Regional partners and distributors
- Local implementation specialists
- Partner capabilities and experience
- Contact priorities and recommendations

### Price Benchmarking
- Market price ranges and estimates
- Total cost of ownership breakdown
- Budget planning recommendations
- Cost factors and considerations

### Implementation Roadmap
- Phase-by-phase implementation approach
- Timeline estimates and milestones
- Resource requirements and dependencies
- Risk mitigation strategies

### Risk Assessment
- Technology, vendor, and implementation risks
- Market and compliance considerations
- Mitigation strategies for each risk category

## 🏗️ Project Structure

```
procurement-discovery-copilot/
├── src/
│   ├── agents/              # Multi-agent system
│   │   ├── clarification_agent.py    # Input validation & clarification
│   │   ├── description_agent.py      # Service description generation
│   │   ├── orchestrator.py           # Workflow coordination
│   │   ├── report_agent.py           # Report compilation
│   │   └── search_agent.py           # Vendor/partner discovery
│   ├── config/
│   │   └── settings.py      # Configuration management
│   ├── models/
│   │   └── state.py         # Data models and workflow state
│   ├── tools/
│   │   └── search_tools.py  # Tavily search integration
│   ├── utils/
│   │   ├── llm_factory.py   # Azure OpenAI model management
│   │   ├── logging.py       # Logging configuration
│   │   └── output_formatter.py  # Multi-format report generation
│   ├── workflow/
│   │   └── procurement_workflow.py  # LangGraph workflow
│   └── main.py              # Main application interface
├── .env.example             # Environment variable template
├── .gitignore              # Git ignore rules
├── pyproject.toml          # Modern Python packaging
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🔧 Advanced Configuration

### Azure OpenAI Model Settings

The application supports fine-tuned control over model behavior:

```env
# Standard Model (GPT-4.1) Settings
LLM_MODEL=gpt-4.1
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=20000

# Reasoning Model (o3) Settings
REASONING_MODEL=o3
REASONING_MAX_COMPLETION_TOKENS=40000
# Note: o3 models don't support temperature parameter

# Task-specific Model Selection
USE_REASONING_MODEL_FOR_ANALYSIS=true
USE_REASONING_MODEL_FOR_COMPLEX_SEARCH=true
```

### Search Configuration

```env
# Tavily Search Settings
TAVILY_API_KEY=your_tavily_api_key
SEARCH_MAX_RESULTS=10

# Workflow Settings
WORKFLOW_MAX_RETRIES=3
```

### Logging Configuration

```env
# Set logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

## 🧪 Testing

Test the system with a quick example:

```bash
# Using uv
uv run python -c "
from src.main import ProcurementDiscoveryApp
app = ProcurementDiscoveryApp()
result = app.discover('CRM Software', 'Germany', 'Manufacturing company')
print('✅ System working correctly!')
"

# Or with activated virtual environment
python -c "
from src.main import ProcurementDiscoveryApp
app = ProcurementDiscoveryApp()
result = app.discover('CRM Software', 'Germany', 'Manufacturing company')
print('✅ System working correctly!')
"
```

Generate a test report:

```bash
# Using uv
uv run python -m src.main "Enterprise CRM Software" "Germany" --details "Manufacturing company with 500 employees" --output test_report.html

# Or with activated virtual environment
python -m src.main "Enterprise CRM Software" "Germany" --details "Manufacturing company with 500 employees" --output test_report.html
```

## 🐛 Troubleshooting

### Common Issues

1. **Azure OpenAI Authentication Errors**
   - Verify `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` in `.env`
   - Ensure your Azure resource has the required model deployments

2. **Model Deployment Issues**
   - Confirm deployment names match `LLM_MODEL` and `REASONING_MODEL` settings
   - Check model availability in your Azure region

3. **o3 Model Parameter Warnings**
   - Warning about `max_completion_tokens` is expected for o3 models
   - o3 models don't support temperature parameter (automatically handled)

4. **Search Quality Issues**
   - Verify `TAVILY_API_KEY` is valid
   - Provide more specific service descriptions for better results

5. **Rate Limiting**
   - The system implements automatic retry with exponential backoff
   - Consider increasing quotas in Azure OpenAI if needed

### Enable Debug Logging

For detailed troubleshooting information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.main import ProcurementDiscoveryApp
app = ProcurementDiscoveryApp()
# ... your code
```

## 🚀 Development

### Setting up Development Environment

1. Clone and set up with uv:
```bash
git clone https://github.com/cpich3g/procurement-discovery-copilot.git
cd procurement-discovery-copilot

# Create virtual environment
uv venv

# Activate virtual environment
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

# Install project in development mode with all dependencies
uv sync --dev
```

2. Install additional development tools:
```bash
uv add --dev pytest black flake8 mypy
```

### Code Quality

Format code:
```bash
uv run black src/
```

Lint code:
```bash
uv run flake8 src/
```

Type checking:
```bash
uv run mypy src/
```

Run tests:
```bash
uv run pytest
```

### Adding New Features

1. **New Agents**: Create in `src/agents/` following existing patterns
2. **New Tools**: Add to `src/tools/` with proper integration
3. **Workflow Changes**: Update `src/workflow/procurement_workflow.py`
4. **Output Formats**: Extend `src/utils/output_formatter.py`

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📞 Support

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and community support
- **Documentation**: Check this README and code comments for detailed information

## 🗺️ Roadmap

- [ ] Web UI interface with React/FastAPI
- [ ] Additional search providers (Google, Bing)
- [ ] Integration with procurement systems (SAP Ariba, Oracle)
- [ ] Advanced analytics and comparison matrices
- [ ] Multi-language support for global procurement
- [ ] RFP generation assistance
- [ ] Vendor risk assessment integration
- [ ] Real-time price monitoring
- [ ] Contract analysis and recommendations
