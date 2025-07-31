"""
Search tools for the Procurement Discovery Tool.

This module provides search capabilities using Tavily API for:
1. Vendor discovery and research
2. Regional partner identification
3. Market intelligence gathering
4. Price benchmarking research
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from tavily import TavilyClient
from pydantic import BaseModel, Field

from ..config.settings import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SearchQuery(BaseModel):
    """Schema for search queries."""
    query: str = Field(description="The search query to execute")
    search_type: str = Field(description="Type of search: vendor, partner, pricing, market")
    max_results: int = Field(default=10, description="Maximum number of results to return")
    include_domains: Optional[List[str]] = Field(default=None, description="Domains to include in search")
    exclude_domains: Optional[List[str]] = Field(default=None, description="Domains to exclude from search")


class SearchResult(BaseModel):
    """Schema for individual search results."""
    title: str
    url: str
    content: str
    score: float
    published_date: Optional[str] = None
    domain: str


class TavilySearchTool:
    """Tavily search tool for procurement research."""
    
    def __init__(self):
        """Initialize the Tavily search tool."""
        self.name = "tavily_search"
        self.description = """
        Search the web for information about vendors, partners, and market intelligence.
        Use this tool to find:
        - Global vendors for specific services/products
        - Regional partners and distributors
        - Market pricing information
        - Company information and profiles
        - Industry trends and analysis
        """
        self._client = TavilyClient(api_key=config.search.tavily_api_key)
        logger.info("Tavily search tool initialized")
    
    @property
    def client(self):
        """Get the Tavily client."""
        if not hasattr(self, '_client') or self._client is None:
            self._client = TavilyClient(api_key=config.search.tavily_api_key)
        return self._client
    
    def run(self, query: str, search_type: str = "general", max_results: int = 10) -> Dict[str, Any]:
        """
        Execute a search query using Tavily.
        
        Args:
            query: The search query to execute
            search_type: Type of search (vendor, partner, pricing, market)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results
        """
        try:
            logger.info(f"Executing Tavily search: {query} (type: {search_type})")
            
            # Customize search parameters based on type
            search_params = {
                "query": query,
                "max_results": min(max_results, config.search.max_results),
                "include_images": config.search.include_images,
                "include_raw_content": config.search.include_raw_content,
                "include_answer": True
            }
            
            # Add domain filters based on search type
            if search_type == "vendor":
                # Focus on company websites and business directories
                search_params["include_domains"] = [
                    "linkedin.com", "bloomberg.com", "reuters.com", 
                    "crunchbase.com", "g2.com", "capterra.com"
                ]
            elif search_type == "partner":
                # Focus on partner directories and local business listings
                search_params["include_domains"] = [
                    "partnerdirectory.com", "yellowpages.com", "chambers.com",
                    "linkedin.com", "local.business"
                ]
            elif search_type == "pricing":
                # Focus on pricing and market research sources
                search_params["include_domains"] = [
                    "gartner.com", "forrester.com", "idc.com", 
                    "pricing.com", "marketresearch.com"
                ]
            
            # Execute the search
            response = self.client.search(**search_params)
            
            # Process results
            results = []
            if "results" in response:
                for result in response["results"][:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        "score": result.get("score", 0.0),
                        "published_date": result.get("published_date"),
                        "domain": self._extract_domain(result.get("url", ""))
                    })
            
            # Prepare response
            search_result = {
                "query": query,
                "search_type": search_type,
                "results": results,
                "answer": response.get("answer", ""),
                "total_results": len(results),
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            logger.info(f"Search completed: {len(results)} results found")
            return search_result
            
        except Exception as e:
            logger.error(f"Error in Tavily search: {str(e)}")
            return {
                "query": query,
                "search_type": search_type,
                "results": [],
                "answer": "",
                "total_results": 0,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    async def arun(self, query: str, search_type: str = "general", max_results: int = 10) -> Dict[str, Any]:
        """Async version of the search function."""
        return self.run(query, search_type, max_results)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""


class SearchQueryGenerator:
    """Generates optimized search queries for different search types."""
    
    @staticmethod
    def generate_vendor_queries(service_name: str, service_category: str, region: str) -> List[str]:
        """Generate search queries for vendor discovery."""
        queries = [
            f"{service_name} vendors companies providers",
            f"{service_name} top vendors {region}",
            f"{service_category} leading companies global",
            f"{service_name} enterprise solutions providers",
            f"best {service_name} vendors comparison",
            f"{service_name} market leaders {region}",
            f"{service_category} vendors directory",
            f"{service_name} implementation partners"
        ]
        return queries[:config.search.max_search_queries]
    
    @staticmethod
    def generate_partner_queries(service_name: str, country: str, vendor_names: List[str] = None) -> List[str]:
        """Generate search queries for partner discovery."""
        queries = [
            f"{service_name} partners {country}",
            f"{service_name} distributors {country}",
            f"{service_name} resellers {country}",
            f"{service_name} implementation partners {country}",
            f"{service_name} local partners {country}"
        ]
        
        # Add vendor-specific partner queries if vendors are known
        if vendor_names:
            for vendor in vendor_names[:3]:  # Limit to top 3 vendors
                queries.extend([
                    f"{vendor} partners {country}",
                    f"{vendor} distributors {country}"
                ])
        
        return queries[:config.search.max_search_queries]
    
    @staticmethod
    def generate_pricing_queries(service_name: str, service_category: str) -> List[str]:
        """Generate search queries for pricing research."""
        queries = [
            f"{service_name} pricing cost",
            f"{service_name} price comparison",
            f"{service_category} market pricing",
            f"{service_name} total cost ownership",
            f"{service_name} pricing model",
            f"{service_category} cost analysis",
            f"{service_name} implementation cost"
        ]
        return queries[:config.search.max_search_queries]
    
    @staticmethod
    def generate_market_queries(service_name: str, service_category: str, region: str) -> List[str]:
        """Generate search queries for market intelligence."""
        queries = [
            f"{service_name} market analysis {region}",
            f"{service_category} market trends",
            f"{service_name} industry report",
            f"{service_category} market size {region}",
            f"{service_name} competitive landscape",
            f"{service_category} market forecast"
        ]
        return queries[:config.search.max_search_queries]


def create_tavily_search_tool() -> TavilySearchTool:
    """Factory function to create a Tavily search tool instance."""
    return TavilySearchTool()
