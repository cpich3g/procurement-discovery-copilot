"""
LLM Factory for creating Azure OpenAI and reasoning model instances.
"""

from typing import Optional, Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain_core.language_models import BaseLanguageModel
from src.config.settings import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LLMFactory:
    """Factory for creating and managing LLM instances."""
    
    def __init__(self):
        """Initialize the LLM factory."""
        self._standard_llm: Optional[BaseLanguageModel] = None
        self._reasoning_llm: Optional[BaseLanguageModel] = None
    
    def get_standard_llm(self, **kwargs) -> BaseLanguageModel:
        """
        Get the standard LLM instance (GPT-4).
        
        Args:
            **kwargs: Additional parameters to override defaults
            
        Returns:
            BaseLanguageModel: Configured LLM instance
        """
        if self._standard_llm is None:
            self._standard_llm = self._create_azure_llm(
                model_name=config.llm.model_name,
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
                **kwargs
            )
        return self._standard_llm
    
    def get_reasoning_llm(self, **kwargs) -> BaseLanguageModel:
        """
        Get the reasoning LLM instance (o3/o3-mini).
        
        Args:
            **kwargs: Additional parameters to override defaults
            
        Returns:
            BaseLanguageModel: Configured reasoning LLM instance
        """
        if self._reasoning_llm is None:
            # Note: o3 models don't support custom temperature parameter
            self._reasoning_llm = self._create_azure_llm(
                model_name=config.llm.reasoning_model,
                temperature=None,  # Will be ignored for reasoning models
                max_tokens=config.llm.reasoning_max_tokens,
                **kwargs
            )
        return self._reasoning_llm
    
    def get_llm_for_task(self, task_type: str, **kwargs) -> BaseLanguageModel:
        """
        Get the appropriate LLM based on task type.
        
        Args:
            task_type: Type of task ('analysis', 'search', 'standard')
            **kwargs: Additional parameters to override defaults
            
        Returns:
            BaseLanguageModel: Appropriate LLM instance
        """
        if task_type == "analysis" and config.llm.use_reasoning_for_analysis:
            logger.info(f"Using reasoning model ({config.llm.reasoning_model}) for analysis task")
            return self.get_reasoning_llm(**kwargs)
        elif task_type == "search" and config.llm.use_reasoning_for_complex_search:
            logger.info(f"Using reasoning model ({config.llm.reasoning_model}) for complex search task")
            return self.get_reasoning_llm(**kwargs)
        else:
            logger.info(f"Using standard model ({config.llm.model_name}) for {task_type} task")
            return self.get_standard_llm(**kwargs)
    
    def _create_azure_llm(
        self,
        model_name: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> BaseLanguageModel:
        """
        Create an Azure OpenAI LLM instance.
        
        Args:
            model_name: Name of the Azure deployment
            temperature: Temperature setting
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            BaseLanguageModel: Configured Azure OpenAI instance
        """
        try:
            # Check if this is a reasoning model (o1, o3, o3-mini, o3-pro, o4-mini)
            is_reasoning_model = any(model_type in model_name.lower() for model_type in 
                                   ['o1', 'o3', 'o4-mini'])
            
            # Base parameters that all models support
            llm_params = {
                "azure_deployment": model_name,
                "api_version": config.llm.azure_api_version,
                "azure_endpoint": config.llm.azure_endpoint,
                "api_key": config.azure_openai_api_key,
                "timeout": config.llm.timeout,
                "max_retries": config.llm.max_retries,
                **kwargs
            }
            
            if is_reasoning_model:
                # Reasoning models: use max_completion_tokens, NO temperature
                llm_params["max_completion_tokens"] = max_tokens
                logger.info(f"Creating Azure OpenAI reasoning model: {model_name} (using max_completion_tokens={max_tokens}, no temperature)")
            else:
                # Standard models: use max_tokens and temperature
                llm_params["max_tokens"] = max_tokens
                llm_params["temperature"] = temperature
                logger.info(f"Creating Azure OpenAI standard model: {model_name} (using max_tokens={max_tokens}, temperature={temperature})")
            
            logger.debug(f"LLM parameters: {self._safe_log_params(llm_params)}")
            
            return AzureChatOpenAI(**llm_params)
            
        except Exception as e:
            logger.error(f"Failed to create Azure OpenAI LLM {model_name}: {str(e)}")
            raise RuntimeError(f"LLM creation failed: {str(e)}")
    
    def _safe_log_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a safe version of parameters for logging (masks API key).
        
        Args:
            params: Original parameters
            
        Returns:
            Dict[str, Any]: Safe parameters for logging
        """
        safe_params = params.copy()
        if "api_key" in safe_params:
            safe_params["api_key"] = "***MASKED***"
        return safe_params
    
    def reset_instances(self):
        """Reset cached LLM instances (useful for testing or config changes)."""
        self._standard_llm = None
        self._reasoning_llm = None
        logger.info("LLM instances reset")


# Global LLM factory instance
llm_factory = LLMFactory()


def get_llm(task_type: str = "standard", **kwargs) -> BaseLanguageModel:
    """
    Convenience function to get an LLM instance.
    
    Args:
        task_type: Type of task ('analysis', 'search', 'standard')
        **kwargs: Additional parameters
        
    Returns:
        BaseLanguageModel: Appropriate LLM instance
    """
    return llm_factory.get_llm_for_task(task_type, **kwargs)


def get_standard_llm(**kwargs) -> BaseLanguageModel:
    """
    Convenience function to get the standard LLM.
    
    Args:
        **kwargs: Additional parameters
        
    Returns:
        BaseLanguageModel: Standard LLM instance
    """
    return llm_factory.get_standard_llm(**kwargs)


def get_reasoning_llm(**kwargs) -> BaseLanguageModel:
    """
    Convenience function to get the reasoning LLM.
    
    Args:
        **kwargs: Additional parameters
        
    Returns:
        BaseLanguageModel: Reasoning LLM instance
    """
    return llm_factory.get_reasoning_llm(**kwargs)
