"""
Clarification Agent for the Procurement Discovery Tool.

This agent is responsible for:
1. Validating user input
2. Clarifying requirements
3. Enriching the request with additional context
4. Ensuring complete and precise input before proceeding
"""

from typing import Dict, Any, List
from datetime import datetime
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..models.state import ProcurementState, ClarificationOutput, ProcessingStatus
from ..config.settings import config
from ..utils.logging import get_logger
from ..utils.llm_factory import get_llm

logger = get_logger(__name__)


class ClarificationResponse(BaseModel):
    """Structured response from the clarification agent."""
    is_valid_request: bool = Field(description="Whether the request is valid for procurement")
    clarified_service_name: str = Field(description="Clarified and standardized service name")
    service_category: str = Field(description="Broad category of the service/product")
    country_code: str = Field(description="ISO country code")
    region: str = Field(description="Geographic region")
    specific_requirements: List[str] = Field(description="List of specific requirements identified")
    business_context: str = Field(description="Business context and use case")
    urgency_level: str = Field(description="Urgency level: low, medium, high, critical")
    budget_range: str = Field(description="Estimated budget range if mentioned")
    technical_requirements: List[str] = Field(description="Technical requirements identified")
    compliance_requirements: List[str] = Field(description="Compliance and regulatory requirements")
    confidence_score: float = Field(description="Confidence in the clarification (0-1)")
    recommendations: List[str] = Field(description="Recommendations for better specification")


class ClarificationAgent:
    """Agent responsible for clarifying and validating procurement requests."""
    
    def __init__(self):
        """Initialize the clarification agent."""
        # Use standard LLM for clarification tasks
        self.llm = get_llm(task_type="standard")
        
        # Set up output parser
        self.parser = PydanticOutputParser(pydantic_object=ClarificationResponse)
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_template(
            """You are a specialized procurement clarification agent. Your role is to analyze and clarify procurement requests to ensure they are complete, accurate, and actionable.

TASK: Analyze the following procurement request and provide a comprehensive clarification.

INPUT DETAILS:
- Service/Product Name: {service_name}
- Country: {country}
- Additional Details: {additional_details}

ANALYSIS REQUIREMENTS:
1. Validate if this is a legitimate procurement request
2. Clarify and standardize the service/product name
3. Identify the service category (e.g., IT Services, Consulting, Software, Hardware, etc.)
4. Normalize the country to ISO code and identify region
5. Extract specific requirements from the description
6. Determine business context and use cases
7. Assess urgency level based on context
8. Identify technical and compliance requirements
9. Provide recommendations for better specification

VALIDATION CRITERIA:
- Reject requests that are:
  * Clearly not procurement-related
  * Requesting illegal or unethical services
  * Too vague to be actionable (assign low confidence)
  * Personal requests not suitable for business procurement

COUNTRY NORMALIZATION:
- Convert country names to proper ISO codes
- Identify the geographic region (North America, Europe, Asia-Pacific, etc.)
- Handle variations in country naming

SERVICE CATEGORIZATION:
Use standard procurement categories like:
- IT Services & Software
- Professional Services & Consulting  
- Manufacturing & Industrial
- Marketing & Communications
- Facilities & Infrastructure
- Finance & Legal Services
- HR & Training Services
- Supply Chain & Logistics

CONFIDENCE SCORING:
- 0.9-1.0: Complete, clear, and specific request
- 0.7-0.8: Good request with minor clarifications needed
- 0.5-0.6: Acceptable but requires significant clarification
- 0.3-0.4: Poor specification, major clarifications needed
- 0.0-0.2: Invalid or non-actionable request

{format_instructions}

Provide your analysis as a structured response following the exact format specified above."""
        )
        
        # Combine prompt with parser
        self.chain = self.prompt | self.llm | self.parser
        
        logger.info("Clarification agent initialized successfully")
    
    def process(self, state: ProcurementState) -> ProcurementState:
        """
        Process the clarification step of the procurement workflow.
        
        Args:
            state: Current procurement state
            
        Returns:
            Updated state with clarification results
        """
        logger.info(f"Starting clarification for session {state['session_id']}")
        
        try:
            # Update processing status
            state["clarification_status"] = ProcessingStatus.IN_PROGRESS
            state["timestamps"]["clarification_start"] = datetime.now()
            
            # Prepare input for the LLM
            input_data = {
                "service_name": state["service_name"],
                "country": state["country"],
                "additional_details": state.get("additional_details", "None provided"),
                "format_instructions": self.parser.get_format_instructions()
            }
            
            # Invoke the clarification chain
            logger.debug(f"Invoking clarification chain with input: {input_data}")
            response = self.chain.invoke(input_data)
            
            # Convert response to dictionary format
            clarification_output = {
                "is_valid_request": response.is_valid_request,
                "clarified_service_name": response.clarified_service_name,
                "service_category": response.service_category,
                "country_code": response.country_code,
                "region": response.region,
                "specific_requirements": response.specific_requirements,
                "business_context": response.business_context,
                "urgency_level": response.urgency_level,
                "budget_range": response.budget_range,
                "technical_requirements": response.technical_requirements,
                "compliance_requirements": response.compliance_requirements,
                "confidence_score": response.confidence_score,
                "recommendations": response.recommendations
            }
            
            # Update state with results
            state["clarified_requirements"] = clarification_output
            state["clarification_status"] = ProcessingStatus.COMPLETED
            state["timestamps"]["clarification_complete"] = datetime.now()
            
            # Determine next step based on validation
            if response.is_valid_request and response.confidence_score >= 0.3:
                state["next_agent"] = "description"
                logger.info(f"Clarification successful. Confidence: {response.confidence_score}")
            else:
                state["clarification_status"] = ProcessingStatus.FAILED
                error_msg = f"Request validation failed. Confidence: {response.confidence_score}"
                state["errors"].append(error_msg)
                logger.warning(error_msg)
            
            # Add warnings for low confidence
            if response.confidence_score < 0.7:
                warning_msg = f"Low confidence clarification ({response.confidence_score}). Consider providing more details."
                state["warnings"].append(warning_msg)
                logger.warning(warning_msg)
            
        except Exception as e:
            logger.error(f"Error in clarification agent: {str(e)}")
            state["clarification_status"] = ProcessingStatus.FAILED
            state["errors"].append(f"Clarification failed: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
        
        return state
    
    def should_retry(self, state: ProcurementState) -> bool:
        """
        Determine if clarification should be retried.
        
        Args:
            state: Current procurement state
            
        Returns:
            True if should retry, False otherwise
        """
        return (
            state["clarification_status"] == ProcessingStatus.FAILED and
            state.get("retry_count", 0) < state.get("max_retries", 3)
        )


def create_clarification_agent() -> ClarificationAgent:
    """Factory function to create a clarification agent instance."""
    return ClarificationAgent()
