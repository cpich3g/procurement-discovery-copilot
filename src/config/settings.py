"""
Configuration management for the Procurement Discovery Tool.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMConfig:
    """Configuration for Language Model settings."""
    provider: str = "azure_openai"  # Changed default to Azure OpenAI
    model_name: str = "gpt-4"
    reasoning_model: str = "o3-mini"
    temperature: float = 0.1
    max_tokens: int = 2000
    reasoning_max_tokens: int = 4000
    timeout: int = 60
    max_retries: int = 3
    
    # Azure OpenAI specific settings
    azure_endpoint: str = ""
    azure_api_version: str = "2024-02-15-preview"
    
    # Reasoning model usage flags
    use_reasoning_for_analysis: bool = True
    use_reasoning_for_complex_search: bool = True
    
    # Note: reasoning_temperature removed - o3 models only support default temperature


@dataclass
class SearchConfig:
    """Configuration for search tool settings."""
    tavily_api_key: str = ""
    max_results: int = 10
    search_timeout: int = 30
    max_search_queries: int = 5
    include_images: bool = False
    include_raw_content: bool = True


@dataclass
class WorkflowConfig:
    """Configuration for workflow settings."""
    max_retries: int = 3
    timeout_seconds: int = 300
    enable_parallel_processing: bool = True
    enable_state_persistence: bool = True
    checkpoint_interval: int = 1


@dataclass
class AppConfig:
    """Main application configuration."""
    # Required fields (no defaults) must come first
    azure_openai_api_key: str  # Changed from openai_api_key
    tavily_api_key: str
    langsmith_api_key: str
    llm: LLMConfig
    search: SearchConfig
    workflow: WorkflowConfig
    
    # Optional fields (with defaults) must come last
    debug_mode: bool = False
    log_level: str = "INFO"
    max_concurrent_requests: int = 10
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        if not self.llm.azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    
    # Required API keys - Updated for Azure OpenAI
    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    tavily_api_key = os.getenv("TAVILY_API_KEY", "")
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "")
    
    # Optional settings
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # LLM configuration - Updated for Azure OpenAI and reasoning models
    llm_config = LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "azure_openai"),
        model_name=os.getenv("LLM_MODEL", "gpt-4"),
        reasoning_model=os.getenv("REASONING_MODEL", "o3-mini"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
        reasoning_max_tokens=int(os.getenv("REASONING_MAX_TOKENS", "4000")),
        timeout=int(os.getenv("LLM_TIMEOUT", "60")),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        use_reasoning_for_analysis=os.getenv("USE_REASONING_MODEL_FOR_ANALYSIS", "true").lower() == "true",
        use_reasoning_for_complex_search=os.getenv("USE_REASONING_MODEL_FOR_COMPLEX_SEARCH", "true").lower() == "true"
    )
    
    # Search configuration
    search_config = SearchConfig(
        tavily_api_key=tavily_api_key,
        max_results=int(os.getenv("SEARCH_MAX_RESULTS", "10")),
        search_timeout=int(os.getenv("SEARCH_TIMEOUT", "30")),
        max_search_queries=int(os.getenv("MAX_SEARCH_QUERIES", "5")),
        include_images=os.getenv("SEARCH_INCLUDE_IMAGES", "false").lower() == "true",
        include_raw_content=os.getenv("SEARCH_INCLUDE_RAW_CONTENT", "true").lower() == "true"
    )
    
    # Workflow configuration
    workflow_config = WorkflowConfig(
        max_retries=int(os.getenv("WORKFLOW_MAX_RETRIES", "3")),
        timeout_seconds=int(os.getenv("WORKFLOW_TIMEOUT", "300")),
        enable_parallel_processing=os.getenv("ENABLE_PARALLEL_PROCESSING", "true").lower() == "true",
        enable_state_persistence=os.getenv("ENABLE_STATE_PERSISTENCE", "true").lower() == "true",
        checkpoint_interval=int(os.getenv("CHECKPOINT_INTERVAL", "1"))
    )
    
    return AppConfig(
        azure_openai_api_key=azure_openai_api_key,
        tavily_api_key=tavily_api_key,
        langsmith_api_key=langsmith_api_key,
        debug_mode=debug_mode,
        log_level=log_level,
        max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
        llm=llm_config,
        search=search_config,
        workflow=workflow_config
    )

# Global configuration instance
config = load_config()
