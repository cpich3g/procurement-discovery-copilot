"""
Report Generation Agent for the Procurement Discovery Tool.

This agent is responsible for:
1. Compiling comprehensive procurement reports
2. Creating vendor comparison matrices
3. Generating price benchmarking analysis
4. Providing implementation roadmaps and recommendations
5. Creating executive summaries
"""

from typing import Dict, Any, List
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..models.state import ProcurementState, FinalReport, PriceAnalysis, ProcessingStatus
from ..config.settings import config
from ..utils.logging import get_logger
from ..utils.llm_factory import get_llm

logger = get_logger(__name__)


class PriceBenchmarkingResponse(BaseModel):
    """Structured response for price benchmarking analysis."""
    price_range_low: float = Field(description="Lower bound of price range")
    price_range_high: float = Field(description="Upper bound of price range")
    currency: str = Field(description="Currency for pricing")
    pricing_model: str = Field(description="Typical pricing model")
    factors_affecting_price: List[str] = Field(description="Key factors that affect pricing")
    total_cost_ownership: List[str] = Field(description="Total cost of ownership factors")
    market_average: float = Field(description="Market average price")
    cost_breakdown: Dict[str, float] = Field(description="Cost breakdown by category")
    recommendations: List[str] = Field(description="Pricing recommendations")


class VendorRankingResponse(BaseModel):
    """Structured response for vendor ranking."""
    vendor_name: str = Field(description="Vendor name")
    overall_score: float = Field(description="Overall ranking score (0-100)")
    strengths: List[str] = Field(description="Key strengths")
    weaknesses: List[str] = Field(description="Potential weaknesses")
    fit_assessment: str = Field(description="Fit assessment for requirements")
    recommendation: str = Field(description="Recommendation level")


class ReportGenerationResponse(BaseModel):
    """Structured response for final report generation."""
    executive_summary: str = Field(description="Executive summary of findings")
    vendor_rankings: List[VendorRankingResponse] = Field(description="Ranked vendor assessments")
    partner_recommendations: List[Dict[str, Any]] = Field(description="Partner recommendations")
    price_benchmarking: PriceBenchmarkingResponse = Field(description="Price analysis")
    implementation_roadmap: List[str] = Field(description="Implementation steps")
    risk_assessment: List[str] = Field(description="Key risks and mitigation strategies")
    next_steps: List[str] = Field(description="Recommended next steps")
    key_findings: List[str] = Field(description="Key findings and insights")


class ReportGenerationAgent:
    """Agent responsible for generating comprehensive procurement reports."""
    
    def __init__(self):
        """Initialize the report generation agent."""
        # Use reasoning model for comprehensive analysis and report generation
        self.llm = get_llm(task_type="analysis")
        
        # Set up output parser
        self.parser = PydanticOutputParser(pydantic_object=ReportGenerationResponse)
        
        # Create the comprehensive report prompt
        self.prompt = ChatPromptTemplate.from_template(
            """You are a senior procurement consultant responsible for generating comprehensive vendor analysis reports. Create a professional, actionable report based on the research findings.

REQUEST DETAILS:
- Service: {service_name}
- Category: {service_category}
- Target Country: {country}
- Region: {region}
- Business Context: {business_context}

SERVICE DESCRIPTION:
{service_description}

VENDOR RESEARCH FINDINGS:
{vendor_findings}

PARTNER RESEARCH FINDINGS:
{partner_findings}

REPORT GENERATION REQUIREMENTS:

1. EXECUTIVE SUMMARY (300-500 words):
   - Brief overview of the procurement request
   - Key findings and recommendations
   - Strategic implications
   - Recommended approach

2. VENDOR RANKINGS:
   For each vendor, provide:
   - Overall score (0-100) based on:
     * Market presence and reputation (25%)
     * Service capability alignment (30%)
     * Geographic coverage (20%)
     * Implementation experience (15%)
     * Innovation and technology (10%)
   - Key strengths and differentiators
   - Potential weaknesses or concerns
   - Fit assessment for specific requirements
   - Recommendation level (Highly Recommended, Recommended, Consider, Not Recommended)

3. PARTNER RECOMMENDATIONS:
   For each partner:
   - Assessment of local capabilities
   - Vendor relationship strength
   - Implementation experience
   - Regional market knowledge
   - Contact priority ranking

4. PRICE BENCHMARKING:
   - Estimated price range (provide realistic ranges)
   - Typical pricing models for this service
   - Factors that influence pricing
   - Total cost of ownership considerations
   - Cost breakdown by major categories
   - Market average estimates
   - Budget planning recommendations

5. IMPLEMENTATION ROADMAP:
   - Phase-by-phase implementation approach
   - Timeline estimates
   - Resource requirements
   - Key milestones
   - Success criteria

6. RISK ASSESSMENT:
   - Technology risks
   - Vendor risks
   - Implementation risks
   - Market risks
   - Mitigation strategies for each

7. NEXT STEPS:
   - Immediate actions recommended
   - Vendor engagement strategy
   - Evaluation criteria development
   - Timeline for procurement process

8. KEY FINDINGS:
   - Market insights
   - Technology trends
   - Competitive dynamics
   - Regional considerations

QUALITY STANDARDS:
- Use professional, executive-level language
- Provide specific, actionable recommendations
- Include realistic timelines and cost estimates
- Base all recommendations on the research findings
- Consider regional and cultural factors
- Ensure compliance with procurement best practices

{format_instructions}

Generate a comprehensive procurement report following the exact format specified above."""
        )
        
        # Combine prompt with parser
        self.chain = self.prompt | self.llm | self.parser
        
        logger.info("Report generation agent initialized successfully")
    
    def process(self, state: ProcurementState) -> ProcurementState:
        """
        Process the report generation step of the procurement workflow.
        
        Args:
            state: Current procurement state
            
        Returns:
            Updated state with final report
        """
        logger.info(f"Starting report generation for session {state['session_id']}")
        
        try:
            # Validate prerequisites
            required_components = ["clarified_requirements", "service_description", "vendor_results"]
            for component in required_components:
                if not state.get(component):
                    raise ValueError(f"Cannot generate report without {component}")
            
            # Update processing status
            state["report_status"] = ProcessingStatus.IN_PROGRESS
            state["timestamps"]["report_start"] = datetime.now()
            
            # Extract information for report generation
            clarified = state["clarified_requirements"]
            service_desc = state["service_description"]
            vendors = state.get("vendor_results", [])
            partners = state.get("partner_results", [])
            
            # Prepare input data
            input_data = {
                "service_name": clarified.get("clarified_service_name", ""),
                "service_category": clarified.get("service_category", ""),
                "country": clarified.get("country_code", ""),
                "region": clarified.get("region", ""),
                "business_context": clarified.get("business_context", ""),
                "service_description": self._format_service_description(service_desc),
                "vendor_findings": self._format_vendor_findings(vendors),
                "partner_findings": self._format_partner_findings(partners),
                "format_instructions": self.parser.get_format_instructions()
            }
            
            # Generate the report
            logger.debug("Invoking report generation chain")
            response = self.chain.invoke(input_data)
            
            # Convert response to final report format
            final_report = {
                "executive_summary": response.executive_summary,
                "service_analysis": service_desc,
                "vendor_rankings": [ranking.dict() for ranking in response.vendor_rankings],
                "partner_recommendations": response.partner_recommendations,
                "price_benchmarking": response.price_benchmarking.dict(),
                "implementation_roadmap": response.implementation_roadmap,
                "risk_assessment": response.risk_assessment,
                "next_steps": response.next_steps,
                "key_findings": response.key_findings,
                "appendices": {
                    "vendor_details": vendors,
                    "partner_details": partners,
                    "search_metadata": {
                        "queries_used": state.get("search_queries_used", []),
                        "sources_consulted": state.get("sources_consulted", [])
                    }
                },
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "session_id": state["session_id"],
                    "processing_time": self._calculate_processing_time(state),
                    "data_sources": ["web_search", "llm_analysis"],
                    "report_version": "1.0"
                }
            }
            
            # Update state with final report
            state["final_report"] = final_report
            state["report_status"] = ProcessingStatus.COMPLETED
            state["timestamps"]["report_complete"] = datetime.now()
            
            logger.info("Report generation completed successfully")
            
        except Exception as e:
            logger.error(f"Error in report generation agent: {str(e)}")
            state["report_status"] = ProcessingStatus.FAILED
            state["errors"].append(f"Report generation failed: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
        
        return state
    
    def _format_service_description(self, service_desc: Dict[str, Any]) -> str:
        """Format service description for report input."""
        if not service_desc:
            return "Service description not available."
        
        formatted = f"""
Overview: {service_desc.get('service_overview', 'N/A')}
Key Features: {', '.join(service_desc.get('key_features', []))}
Use Cases: {', '.join(service_desc.get('use_cases', []))}
Technical Requirements: {', '.join(service_desc.get('technical_specifications', []))}
Compliance Standards: {', '.join(service_desc.get('compliance_standards', []))}
"""
        return formatted.strip()
    
    def _format_vendor_findings(self, vendors: List[Dict[str, Any]]) -> str:
        """Format vendor findings for report input."""
        if not vendors:
            return "No vendor information available."
        
        formatted = []
        for i, vendor in enumerate(vendors[:10], 1):  # Limit to top 10 vendors
            vendor_info = f"""
Vendor {i}: {vendor.get('vendor_name', 'Unknown')}
Description: {vendor.get('description', 'N/A')}
Headquarters: {vendor.get('headquarters', 'N/A')}
Market Position: {vendor.get('market_position', 'N/A')}
Specializations: {', '.join(vendor.get('specializations', []))}
Global Presence: {', '.join(vendor.get('global_presence', []))}
"""
            formatted.append(vendor_info.strip())
        
        return "\n\n".join(formatted)
    
    def _format_partner_findings(self, partners: List[Dict[str, Any]]) -> str:
        """Format partner findings for report input."""
        if not partners:
            return "No partner information available."
        
        formatted = []
        for i, partner in enumerate(partners[:10], 1):  # Limit to top 10 partners
            partner_info = f"""
Partner {i}: {partner.get('partner_name', 'Unknown')}
Location: {partner.get('city', 'N/A')}, {partner.get('country', 'N/A')}
Vendor Relationship: {partner.get('vendor_relationship', 'N/A')}
Specializations: {', '.join(partner.get('specializations', []))}
Local Experience: {partner.get('local_experience', 'N/A')}
"""
            formatted.append(partner_info.strip())
        
        return "\n\n".join(formatted)
    
    def _calculate_processing_time(self, state: ProcurementState) -> str:
        """Calculate total processing time."""
        try:
            start_time = state.get("start_time")
            if start_time:
                duration = datetime.now() - start_time
                return f"{duration.total_seconds():.2f} seconds"
        except:
            pass
        return "Unknown"
    
    def should_retry(self, state: ProcurementState) -> bool:
        """
        Determine if report generation should be retried.
        
        Args:
            state: Current procurement state
            
        Returns:
            True if should retry, False otherwise
        """
        return (
            state["report_status"] == ProcessingStatus.FAILED and
            state.get("retry_count", 0) < state.get("max_retries", 3)
        )


def create_report_generation_agent() -> ReportGenerationAgent:
    """Factory function to create a report generation agent instance."""
    return ReportGenerationAgent()
