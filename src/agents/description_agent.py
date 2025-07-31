"""
Description Agent for the Procurement Discovery Tool.

This agent is responsible for:
1. Generating comprehensive service/product descriptions
2. Identifying technical specifications
3. Listing use cases and benefits
4. Determining compliance requirements
5. Providing implementation considerations
"""

from typing import Dict, Any, List
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..models.state import ProcurementState, ServiceDescription, ProcessingStatus
from ..config.settings import config
from ..utils.logging import get_logger
from ..utils.llm_factory import get_llm

logger = get_logger(__name__)


class ServiceDescriptionResponse(BaseModel):
    """Structured response from the description agent."""
    service_overview: str = Field(description="High-level overview of the service/product")
    detailed_description: str = Field(description="Comprehensive detailed description")
    key_features: List[str] = Field(description="List of key features and capabilities")
    technical_specifications: List[str] = Field(description="Technical requirements and specifications")
    use_cases: List[str] = Field(description="Common use cases and applications")
    industry_applications: List[str] = Field(description="Industry-specific applications")
    benefits: List[str] = Field(description="Business benefits and value proposition")
    implementation_considerations: List[str] = Field(description="Key implementation factors")
    compliance_standards: List[str] = Field(description="Relevant compliance standards and regulations")
    integration_requirements: List[str] = Field(description="Integration and compatibility requirements")
    market_trends: List[str] = Field(description="Current market trends and developments")
    cost_factors: List[str] = Field(description="Factors that influence cost and pricing")


class DescriptionAgent:
    """Agent responsible for generating comprehensive service/product descriptions."""
    
    def __init__(self):
        """Initialize the description agent."""
        # Use reasoning model for complex analysis tasks
        self.llm = get_llm(task_type="analysis")
        
        # Set up output parser
        self.parser = PydanticOutputParser(pydantic_object=ServiceDescriptionResponse)
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_template(
            """You are a specialized procurement service description agent. Your role is to generate comprehensive, accurate, and actionable descriptions of services and products for procurement purposes.

TASK: Generate a detailed service/product description based on the clarified requirements.

CLARIFIED REQUIREMENTS:
- Service Name: {clarified_service_name}
- Service Category: {service_category}
- Business Context: {business_context}
- Specific Requirements: {specific_requirements}
- Technical Requirements: {technical_requirements}
- Compliance Requirements: {compliance_requirements}
- Country/Region: {country_code} ({region})
- Urgency Level: {urgency_level}

DESCRIPTION REQUIREMENTS:
1. SERVICE OVERVIEW: Provide a clear, concise overview that explains what the service/product is and its primary purpose.

2. DETAILED DESCRIPTION: Write a comprehensive description that covers:
   - Core functionality and capabilities
   - How it works at a high level
   - Key components or modules
   - Service delivery models (if applicable)

3. KEY FEATURES: List 5-10 essential features that define this service/product.

4. TECHNICAL SPECIFICATIONS: Include relevant technical details such as:
   - System requirements
   - Performance specifications
   - Scalability considerations
   - Technology stack (if applicable)
   - Security features

5. USE CASES: Describe 5-8 common scenarios where this service/product is used.

6. INDUSTRY APPLICATIONS: Identify specific industries that commonly use this service/product.

7. BENEFITS: List key business benefits including:
   - Operational improvements
   - Cost savings potential
   - Risk mitigation
   - Competitive advantages

8. IMPLEMENTATION CONSIDERATIONS: Cover important factors like:
   - Implementation timeline
   - Resource requirements
   - Change management needs
   - Training requirements

9. COMPLIANCE STANDARDS: List relevant standards, regulations, and certifications:
   - Industry-specific compliance (GDPR, HIPAA, SOX, etc.)
   - Quality standards (ISO, etc.)
   - Security certifications
   - Regional regulatory requirements for {region}

10. INTEGRATION REQUIREMENTS: Describe:
    - System integration capabilities
    - API requirements
    - Data migration needs
    - Compatibility considerations

11. MARKET TRENDS: Highlight current trends affecting this service/product.

12. COST FACTORS: Identify key factors that influence pricing:
    - Licensing models
    - Implementation costs
    - Ongoing operational costs
    - Scalability cost implications

QUALITY GUIDELINES:
- Use professional, clear language suitable for procurement stakeholders
- Be specific and actionable rather than generic
- Focus on procurement-relevant information
- Consider the specific region and compliance requirements
- Ensure accuracy and avoid speculation
- Structure information logically and comprehensively

{format_instructions}

Generate a comprehensive service description following the exact format specified above."""
        )
        
        # Combine prompt with parser
        self.chain = self.prompt | self.llm | self.parser
        
        logger.info("Description agent initialized successfully")
    
    def process(self, state: ProcurementState) -> ProcurementState:
        """
        Process the description step of the procurement workflow.
        
        Args:
            state: Current procurement state
            
        Returns:
            Updated state with description results
        """
        logger.info(f"Starting description generation for session {state['session_id']}")
        
        try:
            # Validate that clarification is complete
            if not state.get("clarified_requirements"):
                raise ValueError("Cannot generate description without completed clarification")
            
            # Update processing status
            state["description_status"] = ProcessingStatus.IN_PROGRESS
            state["timestamps"]["description_start"] = datetime.now()
            
            # Extract clarified requirements
            clarified = state["clarified_requirements"]
            
            # Prepare input for the LLM
            input_data = {
                "clarified_service_name": clarified.get("clarified_service_name", ""),
                "service_category": clarified.get("service_category", ""),
                "business_context": clarified.get("business_context", ""),
                "specific_requirements": ", ".join(clarified.get("specific_requirements", [])),
                "technical_requirements": ", ".join(clarified.get("technical_requirements", [])),
                "compliance_requirements": ", ".join(clarified.get("compliance_requirements", [])),
                "country_code": clarified.get("country_code", ""),
                "region": clarified.get("region", ""),
                "urgency_level": clarified.get("urgency_level", ""),
                "format_instructions": self.parser.get_format_instructions()
            }
            
            # Invoke the description chain
            logger.debug(f"Invoking description chain for service: {clarified.get('clarified_service_name')}")
            response = self.chain.invoke(input_data)
            
            # Convert response to dictionary format
            description_output = {
                "service_overview": response.service_overview,
                "detailed_description": response.detailed_description,
                "key_features": response.key_features,
                "technical_specifications": response.technical_specifications,
                "use_cases": response.use_cases,
                "industry_applications": response.industry_applications,
                "benefits": response.benefits,
                "implementation_considerations": response.implementation_considerations,
                "compliance_standards": response.compliance_standards,
                "integration_requirements": response.integration_requirements,
                "market_trends": response.market_trends,
                "cost_factors": response.cost_factors
            }
            
            # Update state with results
            state["service_description"] = description_output
            state["description_status"] = ProcessingStatus.COMPLETED
            state["timestamps"]["description_complete"] = datetime.now()
            state["next_agent"] = "search"
            
            logger.info(f"Description generation completed successfully for {clarified.get('clarified_service_name')}")
            
        except Exception as e:
            logger.error(f"Error in description agent: {str(e)}")
            state["description_status"] = ProcessingStatus.FAILED
            state["errors"].append(f"Description generation failed: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
        
        return state
    
    def should_retry(self, state: ProcurementState) -> bool:
        """
        Determine if description generation should be retried.
        
        Args:
            state: Current procurement state
            
        Returns:
            True if should retry, False otherwise
        """
        return (
            state["description_status"] == ProcessingStatus.FAILED and
            state.get("retry_count", 0) < state.get("max_retries", 3)
        )


def create_description_agent() -> DescriptionAgent:
    """Factory function to create a description agent instance."""
    return DescriptionAgent()
