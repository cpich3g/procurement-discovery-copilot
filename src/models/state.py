"""
State definitions for the Procurement Discovery Tool.
"""

from typing import Dict, List, Optional, TypedDict, Any
from datetime import datetime
from enum import Enum


class ProcessingStatus(Enum):
    """Processing status for each stage of the workflow."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcurementState(TypedDict):
    """
    Main state object for the procurement discovery workflow.
    This state is passed between all agents in the LangGraph workflow.
    """
    # Input data
    service_name: str
    country: str
    additional_details: Optional[str]
    
    # Processing status tracking
    clarification_status: ProcessingStatus
    description_status: ProcessingStatus
    search_status: ProcessingStatus
    report_status: ProcessingStatus
    
    # Agent outputs
    clarified_requirements: Optional[Dict[str, Any]]
    service_description: Optional[Dict[str, Any]]
    vendor_results: Optional[List[Dict[str, Any]]]
    partner_results: Optional[List[Dict[str, Any]]]
    price_analysis: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    
    # Metadata
    session_id: str
    start_time: datetime
    timestamps: Dict[str, datetime]
    errors: List[str]
    warnings: List[str]
    
    # Flow control
    next_agent: Optional[str]
    retry_count: int
    max_retries: int


class ClarificationOutput(TypedDict):
    """Output schema for the Clarification Agent."""
    is_valid_request: bool
    clarified_service_name: str
    service_category: str
    country_code: str
    region: str
    specific_requirements: List[str]
    business_context: str
    urgency_level: str
    budget_range: Optional[str]
    technical_requirements: List[str]
    compliance_requirements: List[str]


class ServiceDescription(TypedDict):
    """Output schema for the Description Agent."""
    service_overview: str
    detailed_description: str
    key_features: List[str]
    technical_specifications: List[str]
    use_cases: List[str]
    industry_applications: List[str]
    benefits: List[str]
    implementation_considerations: List[str]
    compliance_standards: List[str]
    integration_requirements: List[str]


class VendorInfo(TypedDict):
    """Schema for vendor information."""
    vendor_name: str
    description: str
    website: Optional[str]
    headquarters: str
    global_presence: List[str]
    specializations: List[str]
    market_position: str
    company_size: str
    year_established: Optional[int]
    key_clients: List[str]
    certifications: List[str]
    contact_info: Optional[Dict[str, str]]


class PartnerInfo(TypedDict):
    """Schema for regional partner information."""
    partner_name: str
    vendor_relationship: str
    country: str
    city: str
    description: str
    specializations: List[str]
    certifications: List[str]
    contact_info: Dict[str, str]
    local_experience: str
    client_references: List[str]


class PriceAnalysis(TypedDict):
    """Schema for price benchmarking analysis."""
    price_range_low: Optional[float]
    price_range_high: Optional[float]
    currency: str
    pricing_model: str
    factors_affecting_price: List[str]
    total_cost_ownership: List[str]
    market_average: Optional[float]
    cost_breakdown: Dict[str, float]
    recommendations: List[str]


class SearchResults(TypedDict):
    """Schema for search agent results."""
    vendors: List[VendorInfo]
    partners: List[PartnerInfo]
    search_queries_used: List[str]
    sources_consulted: List[str]
    confidence_score: float
    search_timestamp: datetime


class FinalReport(TypedDict):
    """Schema for the final report output."""
    executive_summary: str
    service_analysis: ServiceDescription
    vendor_rankings: List[Dict[str, Any]]
    partner_recommendations: List[Dict[str, Any]]
    price_benchmarking: PriceAnalysis
    implementation_roadmap: List[str]
    risk_assessment: List[str]
    next_steps: List[str]
    appendices: Dict[str, Any]
    generation_metadata: Dict[str, Any]
