# Procurement Discovery Tool

An AI-powered procurement discovery tool built with LangChain and LangGraph that automates vendor and partner discovery for procurement teams.

## 🚀 Features

- **AI-Powered Service Clarification**: Automatically clarifies and enriches procurement requests
- **Comprehensive Service Descriptions**: Generates detailed technical specifications and requirements
- **Global Vendor Discovery**: Identifies and ranks leading vendors using web search
- **Regional Partner Identification**: Finds local partners and distributors
- **Price Benchmarking**: Provides realistic market pricing analysis
- **Comprehensive Reports**: Generates actionable procurement reports with recommendations
- **Azure OpenAI Integration**: Supports Azure OpenAI with intelligent model selection
- **Reasoning Model Support**: Uses o3/o3-mini models for complex analysis tasks

## 🏗️ Architecture

The system uses a multi-agent architecture built on LangGraph:

- **Orchestrator/Router Agent**: Manages workflow coordination
- **Clarification Agent**: Validates and enriches input requirements (GPT-4)
- **Description Agent**: Generates comprehensive service descriptions (o3/o3-mini)
- **Search Agent**: Discovers vendors and partners using Tavily search (o3/o3-mini)
- **Report Generation Agent**: Compiles comprehensive procurement reports (o3/o3-mini)

### 🧠 Intelligent Model Selection

The system automatically selects the best model for each task:
- **Standard Tasks**: GPT-4 for input validation and basic processing
- **Analysis Tasks**: o3/o3-mini for complex reasoning and analysis
- **Search Tasks**: o3/o3-mini for sophisticated search result interpretation

## ⚡ Quick Start

### Prerequisites

- Python 3.9 or higher
- Azure OpenAI resource with deployed models:
  - GPT-4 (gpt-4) for standard tasks
  - o3-mini (o3-mini) for reasoning tasks
- Tavily API key (for web search)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd procurement-discovery
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials:
# - AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
# - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
# - TAVILY_API_KEY: Your Tavily search API key
# - Model deployment names in Azure OpenAI
```

4. Test the integration:
```bash
python test_azure_integration.py
```
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Azure OpenAI configuration
```

### Usage

#### Command Line Interface

Basic usage:
```bash
python -m src.main "Cloud Storage" "United States"
```

With additional details:
```bash
python -m src.main "ERP Software" "Germany" --details "Manufacturing company with 500 employees"
```

Save results to different formats:
```bash
# JSON format (default)
python -m src.main "Marketing Automation" "Canada" --output results.json

# HTML report with professional styling
python -m src.main "CRM Software" "UK" --output report.html

# Markdown documentation
python -m src.main "Video Conferencing" "Australia" --output summary.md
```

#### Python API

```python
from src.main import ProcurementDiscoveryApp

app = ProcurementDiscoveryApp()

results = app.discover(
    service_name="Cloud Storage",
    country="United States",
    additional_details="Enterprise-grade with compliance requirements"
)

print(results)
```

#### Async Usage

```python
import asyncio
from src.main import ProcurementDiscoveryApp

async def main():
    app = ProcurementDiscoveryApp()
    
    results = await app.adiscover(
        service_name="CRM Software", 
        country="United Kingdom"
    )
    
    return results

results = asyncio.run(main())
```

## 🔧 Configuration

The application can be configured via environment variables in the `.env` file:

### Required Settings

- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
- `TAVILY_API_KEY`: Your Tavily search API key

### Model Configuration

- `LLM_MODEL`: Azure deployment name for GPT-4 (default: gpt-4)
- `REASONING_MODEL`: Azure deployment name for reasoning model (default: o3-mini)
- `LLM_TEMPERATURE`: Standard model temperature (default: 0.1)
- `REASONING_TEMPERATURE`: Reasoning model temperature (default: 0.0)

### Model Selection Settings

- `USE_REASONING_MODEL_FOR_ANALYSIS`: Use o3/o3-mini for analysis tasks (default: true)
- `USE_REASONING_MODEL_FOR_COMPLEX_SEARCH`: Use o3/o3-mini for search analysis (default: true)

### Optional Settings

- `AZURE_OPENAI_API_VERSION`: API version (default: 2024-02-15-preview)
- `LLM_MAX_TOKENS`: Maximum tokens for standard model (default: 2000)
- `REASONING_MAX_TOKENS`: Maximum tokens for reasoning model (default: 4000)
- `SEARCH_MAX_RESULTS`: Maximum search results per query (default: 10)
- `WORKFLOW_MAX_RETRIES`: Maximum retry attempts (default: 3)

### 🔄 Migration from OpenAI

If you're migrating from OpenAI to Azure OpenAI, see the [Azure Migration Guide](AZURE_MIGRATION_GUIDE.md) for detailed instructions.

## Output Format

The tool generates comprehensive reports including:

### Executive Summary
- High-level overview and key recommendations
- Strategic implications and approach

### Vendor Analysis
- Ranked list of global vendors
- Detailed vendor profiles and capabilities
- Fit assessment for specific requirements

### Partner Recommendations  
- Regional partners and distributors
- Local implementation specialists
- Contact information and priorities

### Price Benchmarking
- Market price ranges and estimates
- Total cost of ownership factors
- Budget planning recommendations

### Implementation Roadmap
- Phase-by-phase approach
- Timeline estimates and milestones
- Resource requirements

## Project Structure

```
procurement-discovery/
├── src/
│   ├── agents/           # Individual agent implementations
│   ├── config/           # Configuration management
│   ├── models/           # Data models and state definitions
│   ├── tools/            # Search and utility tools
│   ├── utils/            # Utility functions
│   ├── workflow/         # LangGraph workflow implementation
│   └── main.py           # Main application interface
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variable template
└── README.md            # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
flake8 src/
```

### Adding New Agents

1. Create agent class in `src/agents/`
2. Implement process method following the pattern
3. Add to workflow in `src/workflow/procurement_workflow.py`
4. Update state models if needed

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all required API keys are set in `.env`
2. **Rate Limits**: The tool implements automatic retry with exponential backoff
3. **Search Quality**: Low-quality results may indicate need for more specific requirements

### Logging

Enable verbose logging for debugging:
```bash
python -m src.main "Service Name" "Country" --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support, please open an issue in the repository.

## Roadmap

- [ ] Web UI interface
- [ ] Additional search providers
- [ ] Integration with procurement systems
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Vendor comparison matrices
- [ ] RFP generation assistance
