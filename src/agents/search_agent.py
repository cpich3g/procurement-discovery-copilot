"""
Search Agent for the Procurement Discovery Tool.

This agent is responsible for:
1. Discovering global vendors for specified services
2. Finding regional partners and distributors
3. Gathering market intelligence and pricing information
4. Ranking and validating search results
"""

from typing import Dict, Any, List
from datetime import datetime
import asyncio

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..models.state import ProcurementState, VendorInfo, PartnerInfo, SearchResults, ProcessingStatus
from ..config.settings import config
from ..tools.search_tools import TavilySearchTool, SearchQueryGenerator
from ..utils.logging import get_logger
from ..utils.llm_factory import get_llm

logger = get_logger(__name__)


class VendorAnalysisResponse(BaseModel):
    """Structured response for vendor analysis."""
    vendors: List[VendorInfo] = Field(description="List of identified vendors")
    confidence_score: float = Field(description="Overall confidence in the results (0-1)")
    search_quality: str = Field(description="Quality assessment of search results")
    recommendations: List[str] = Field(description="Recommendations for further research")


class PartnerAnalysisResponse(BaseModel):
    """Structured response for partner analysis."""
    partners: List[PartnerInfo] = Field(description="List of identified regional partners")
    coverage_assessment: str = Field(description="Assessment of regional coverage")
    confidence_score: float = Field(description="Overall confidence in the results (0-1)")
    recommendations: List[str] = Field(description="Recommendations for partner engagement")


class SearchAgent:
    """Agent responsible for vendor and partner discovery through web search."""
    
    def __init__(self):
        """Initialize the search agent."""
        # Use reasoning model for complex search analysis
        self.llm = get_llm(task_type="search")
        
        # Initialize search tool
        self.search_tool = TavilySearchTool()
        self.query_generator = SearchQueryGenerator()
        
        # Set up output parsers
        self.vendor_parser = PydanticOutputParser(pydantic_object=VendorAnalysisResponse)
        self.partner_parser = PydanticOutputParser(pydantic_object=PartnerAnalysisResponse)
        
        # Create prompt templates
        self.vendor_prompt = ChatPromptTemplate.from_template(
            """You are a specialized procurement research analyst. Analyze the search results to identify and rank global vendors for the specified service.

SERVICE DETAILS:
- Service Name: {service_name}
- Service Category: {service_category}
- Region: {region}
- Requirements: {requirements}

SEARCH RESULTS:
{search_results}

ANALYSIS TASK:
Analyze the search results to identify legitimate, established vendors for this service. For each vendor, extract:

1. VENDOR IDENTIFICATION:
   - Company name (exact, official name)
   - Brief description of their services
   - Website URL if available
   - Headquarters location

2. COMPANY PROFILE:
   - Global presence and regions served
   - Service specializations relevant to the requirement
   - Market position (leader, challenger, niche, etc.)
   - Company size (enterprise, mid-market, small)
   - Year established (if available)

3. CREDIBILITY INDICATORS:
   - Key clients or case studies mentioned
   - Industry certifications or partnerships
   - Awards or recognition

4. RELEVANCE ASSESSMENT:
   - How well they match the specific requirements
   - Geographic coverage for the target region
   - Service capabilities alignment

QUALITY CRITERIA:
- Only include established, legitimate companies
- Prioritize vendors with clear relevance to the service
- Exclude generic results, job postings, or non-vendor content
- Focus on companies that actually provide the specified service
- Rank by relevance, reputation, and market presence

CONFIDENCE SCORING:
- 0.9-1.0: Excellent results with clear, established vendors
- 0.7-0.8: Good results with mostly relevant vendors
- 0.5-0.6: Mixed results with some relevant vendors
- 0.3-0.4: Poor results with limited vendor information
- 0.0-0.2: No useful vendor information found

{vendor_format_instructions}

Provide your analysis following the exact format specified above."""
        )
        
        self.partner_prompt = ChatPromptTemplate.from_template(
            """You are a specialized regional partner research analyst. Analyze the search results to identify local/regional partners for the specified vendors and services.

SERVICE DETAILS:
- Service Name: {service_name}
- Target Country: {country}
- Region: {region}
- Known Vendors: {vendor_names}

SEARCH RESULTS:
{search_results}

ANALYSIS TASK:
Analyze the search results to identify legitimate regional partners, distributors, or implementation specialists. For each partner, extract:

1. PARTNER IDENTIFICATION:
   - Company name
   - Relationship to vendor (partner, distributor, reseller, etc.)
   - Location (country, city)
   - Brief description of services

2. CAPABILITIES:
   - Service specializations
   - Local market experience
   - Industry certifications
   - Technical capabilities

3. CONTACT INFORMATION:
   - Website URL
   - Contact details if available
   - Office locations

4. CREDIBILITY:
   - Client references or case studies
   - Years in business
   - Partnership status/levels
   - Local market reputation

QUALITY CRITERIA:
- Focus on legitimate, established local businesses
- Prioritize official partners over general service providers
- Include implementation specialists and consultants
- Exclude individual contractors or non-business entities
- Verify relevance to the specific service and location

COVERAGE ASSESSMENT:
Evaluate how well the identified partners cover the target market:
- Geographic coverage within the country
- Service capability coverage
- Market segment coverage (enterprise, SMB, etc.)
- Gaps that may need additional research

{partner_format_instructions}

Provide your analysis following the exact format specified above."""
        )
        
        logger.info("Search agent initialized successfully")
    
    def process(self, state: ProcurementState) -> ProcurementState:
        """
        Process the search step of the procurement workflow.
        
        Args:
            state: Current procurement state
            
        Returns:
            Updated state with search results
        """
        logger.info(f"Starting search process for session {state['session_id']}")
        
        try:
            # Validate prerequisites
            if not state.get("clarified_requirements") or not state.get("service_description"):
                raise ValueError("Cannot perform search without completed clarification and description")
            
            # Update processing status
            state["search_status"] = ProcessingStatus.IN_PROGRESS
            state["timestamps"]["search_start"] = datetime.now()
            
            # Extract required information
            clarified = state["clarified_requirements"]
            service_name = clarified.get("clarified_service_name", "")
            service_category = clarified.get("service_category", "")
            country = clarified.get("country_code", "")
            region = clarified.get("region", "")
            
            # Perform vendor search
            logger.info("Starting vendor discovery")
            vendor_results = self._search_vendors(service_name, service_category, region)
            
            # Perform partner search
            logger.info("Starting partner discovery")
            vendor_names = [v.get("vendor_name", "") for v in vendor_results.get("vendors", [])]
            partner_results = self._search_partners(service_name, country, region, vendor_names)
            
            # Update state with results
            state["vendor_results"] = vendor_results.get("vendors", [])
            state["partner_results"] = partner_results.get("partners", [])
            
            # Create combined search results
            search_results = {
                "vendors": vendor_results.get("vendors", []),
                "partners": partner_results.get("partners", []),
                "search_queries_used": vendor_results.get("queries_used", []) + partner_results.get("queries_used", []),
                "sources_consulted": vendor_results.get("sources", []) + partner_results.get("sources", []),
                "confidence_score": (vendor_results.get("confidence", 0) + partner_results.get("confidence", 0)) / 2,
                "search_timestamp": datetime.now()
            }
            
            state["search_status"] = ProcessingStatus.COMPLETED
            state["timestamps"]["search_complete"] = datetime.now()
            state["next_agent"] = "report"
            
            logger.info(f"Search completed: {len(vendor_results.get('vendors', []))} vendors, {len(partner_results.get('partners', []))} partners found")
            
        except Exception as e:
            logger.error(f"Error in search agent: {str(e)}")
            state["search_status"] = ProcessingStatus.FAILED
            state["errors"].append(f"Search failed: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
        
        return state
    
    def _search_vendors(self, service_name: str, service_category: str, region: str) -> Dict[str, Any]:
        """Search for global vendors."""
        try:
            # Generate vendor search queries
            queries = self.query_generator.generate_vendor_queries(service_name, service_category, region)
            
            # Execute searches
            all_results = []
            sources = []
            
            for query in queries:
                result = self.search_tool.run(query, "vendor")
                if result.get("success"):
                    all_results.extend(result.get("results", []))
                    sources.extend([r.get("url", "") for r in result.get("results", [])])
            
            # Combine and format search results for analysis
            search_text = self._format_search_results(all_results)
            
            # Analyze results with LLM
            input_data = {
                "service_name": service_name,
                "service_category": service_category,
                "region": region,
                "requirements": "Global vendor discovery",
                "search_results": search_text,
                "vendor_format_instructions": self.vendor_parser.get_format_instructions()
            }
            
            vendor_chain = self.vendor_prompt | self.llm | self.vendor_parser
            analysis = vendor_chain.invoke(input_data)
            
            # Handle both dict and Pydantic model formats
            vendors_list = []
            if hasattr(analysis, 'vendors'):
                for vendor in analysis.vendors:
                    if hasattr(vendor, 'dict'):
                        vendors_list.append(vendor.dict())
                    else:
                        vendors_list.append(vendor)
            
            return {
                "vendors": vendors_list,
                "confidence": getattr(analysis, 'confidence_score', 0.0),
                "queries_used": queries,
                "sources": list(set(sources)),
                "quality_assessment": getattr(analysis, 'search_quality', "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error in vendor search: {str(e)}")
            return {"vendors": [], "confidence": 0.0, "queries_used": [], "sources": []}
    
    def _search_partners(self, service_name: str, country: str, region: str, vendor_names: List[str]) -> Dict[str, Any]:
        """Search for regional partners."""
        try:
            # Generate partner search queries
            queries = self.query_generator.generate_partner_queries(service_name, country, vendor_names)
            
            # Execute searches
            all_results = []
            sources = []
            
            for query in queries:
                result = self.search_tool.run(query, "partner")
                if result.get("success"):
                    all_results.extend(result.get("results", []))
                    sources.extend([r.get("url", "") for r in result.get("results", [])])
            
            # Combine and format search results for analysis
            search_text = self._format_search_results(all_results)
            
            # Analyze results with LLM
            input_data = {
                "service_name": service_name,
                "country": country,
                "region": region,
                "vendor_names": ", ".join(vendor_names[:5]),  # Limit to top 5
                "search_results": search_text,
                "partner_format_instructions": self.partner_parser.get_format_instructions()
            }
            
            partner_chain = self.partner_prompt | self.llm | self.partner_parser
            analysis = partner_chain.invoke(input_data)
            
            # Handle both dict and Pydantic model formats
            partners_list = []
            if hasattr(analysis, 'partners'):
                for partner in analysis.partners:
                    if hasattr(partner, 'dict'):
                        partners_list.append(partner.dict())
                    else:
                        partners_list.append(partner)
            
            return {
                "partners": partners_list,
                "confidence": getattr(analysis, 'confidence_score', 0.0),
                "queries_used": queries,
                "sources": list(set(sources)),
                "coverage_assessment": getattr(analysis, 'coverage_assessment', "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error in partner search: {str(e)}")
            return {"partners": [], "confidence": 0.0, "queries_used": [], "sources": []}
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for LLM analysis."""
        if not results:
            return "No search results available."
        
        formatted = []
        for i, result in enumerate(results[:20], 1):  # Limit to top 20 results
            formatted.append(f"""
Result {i}:
Title: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Content: {result.get('content', 'N/A')[:500]}...
Score: {result.get('score', 0)}
""")
        
        return "\n".join(formatted)
    
    def should_retry(self, state: ProcurementState) -> bool:
        """
        Determine if search should be retried.
        
        Args:
            state: Current procurement state
            
        Returns:
            True if should retry, False otherwise
        """
        return (
            state["search_status"] == ProcessingStatus.FAILED and
            state.get("retry_count", 0) < state.get("max_retries", 3)
        )


def create_search_agent() -> SearchAgent:
    """Factory function to create a search agent instance."""
    return SearchAgent()
