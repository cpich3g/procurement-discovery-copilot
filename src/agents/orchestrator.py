"""
Orchestrator Agent for the Procurement Discovery Tool.

This agent is responsible for:
1. Managing the overall workflow execution
2. Routing between different agents
3. Handling workflow control and decision making
4. Managing error recovery and retries
5. Coordinating parallel executions where applicable
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ..models.state import ProcurementState, ProcessingStatus
from ..config.settings import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WorkflowOrchestrator:
    """Orchestrator responsible for managing the procurement discovery workflow."""
    
    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.workflow_steps = [
            "clarification",
            "description", 
            "search",
            "report"
        ]
        
        self.parallel_steps = {
            # Description and initial market research could potentially run in parallel
            # For now, keeping sequential for clarity and dependency management
        }
        
        logger.info("Workflow orchestrator initialized successfully")
    
    def create_initial_state(
        self, 
        service_name: str, 
        country: str, 
        additional_details: Optional[str] = None
    ) -> ProcurementState:
        """
        Create the initial state for a new procurement discovery session.
        
        Args:
            service_name: Name of the service/product to discover
            country: Target country for procurement
            additional_details: Optional additional details
            
        Returns:
            Initial ProcurementState
        """
        session_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        initial_state: ProcurementState = {
            # Input data
            "service_name": service_name.strip(),
            "country": country.strip(),
            "additional_details": additional_details.strip() if additional_details else None,
            
            # Processing status tracking
            "clarification_status": ProcessingStatus.PENDING,
            "description_status": ProcessingStatus.PENDING,
            "search_status": ProcessingStatus.PENDING,
            "report_status": ProcessingStatus.PENDING,
            
            # Agent outputs (initialized as None)
            "clarified_requirements": None,
            "service_description": None,
            "vendor_results": None,
            "partner_results": None,
            "price_analysis": None,
            "final_report": None,
            
            # Metadata
            "session_id": session_id,
            "start_time": current_time,
            "timestamps": {
                "workflow_start": current_time
            },
            "errors": [],
            "warnings": [],
            
            # Flow control
            "next_agent": "clarification",
            "retry_count": 0,
            "max_retries": config.workflow.max_retries
        }
        
        logger.info(f"Created new procurement session {session_id} for service '{service_name}' in {country}")
        return initial_state
    
    def determine_next_step(self, state: ProcurementState) -> Optional[str]:
        """
        Determine the next step in the workflow based on current state.
        
        Args:
            state: Current procurement state
            
        Returns:
            Name of next agent to execute, or None if workflow is complete
        """
        # Check if we have a specific next agent set
        if state.get("next_agent"):
            return state["next_agent"]
        
        # Determine next step based on completion status
        if state["clarification_status"] != ProcessingStatus.COMPLETED:
            return "clarification"
        elif state["description_status"] != ProcessingStatus.COMPLETED:
            return "description"
        elif state["search_status"] != ProcessingStatus.COMPLETED:
            return "search"
        elif state["report_status"] != ProcessingStatus.COMPLETED:
            return "report"
        else:
            # All steps completed
            return None
    
    def is_workflow_complete(self, state: ProcurementState) -> bool:
        """
        Check if the workflow has completed successfully.
        
        Args:
            state: Current procurement state
            
        Returns:
            True if workflow is complete, False otherwise
        """
        required_statuses = [
            state["clarification_status"],
            state["description_status"], 
            state["search_status"],
            state["report_status"]
        ]
        
        return all(status == ProcessingStatus.COMPLETED for status in required_statuses)
    
    def has_workflow_failed(self, state: ProcurementState) -> bool:
        """
        Check if the workflow has failed beyond recovery.
        
        Args:
            state: Current procurement state
            
        Returns:
            True if workflow has failed, False otherwise
        """
        # Check if any step has failed and exceeded retry limits
        failed_statuses = [
            state["clarification_status"],
            state["description_status"],
            state["search_status"], 
            state["report_status"]
        ]
        
        has_failures = any(status == ProcessingStatus.FAILED for status in failed_statuses)
        exceeded_retries = state.get("retry_count", 0) >= state.get("max_retries", 3)
        
        return has_failures and exceeded_retries
    
    def can_retry_step(self, state: ProcurementState, step_name: str) -> bool:
        """
        Check if a specific step can be retried.
        
        Args:
            state: Current procurement state
            step_name: Name of the step to check
            
        Returns:
            True if step can be retried, False otherwise
        """
        status_key = f"{step_name}_status"
        if status_key not in state:
            return False
        
        is_failed = state[status_key] == ProcessingStatus.FAILED
        under_retry_limit = state.get("retry_count", 0) < state.get("max_retries", 3)
        
        return is_failed and under_retry_limit
    
    def prepare_retry(self, state: ProcurementState, step_name: str) -> ProcurementState:
        """
        Prepare state for retrying a failed step.
        
        Args:
            state: Current procurement state
            step_name: Name of the step to retry
            
        Returns:
            Updated state prepared for retry
        """
        # Reset the status of the failed step
        status_key = f"{step_name}_status"
        state[status_key] = ProcessingStatus.PENDING
        
        # Clear the next agent to allow normal flow determination
        state["next_agent"] = step_name
        
        # Add retry timestamp
        state["timestamps"][f"{step_name}_retry_{state.get('retry_count', 0)}"] = datetime.now()
        
        logger.info(f"Prepared retry for step '{step_name}' (attempt {state.get('retry_count', 0) + 1})")
        return state
    
    def validate_state_integrity(self, state: ProcurementState) -> List[str]:
        """
        Validate the integrity of the workflow state.
        
        Args:
            state: Current procurement state
            
        Returns:
            List of validation errors (empty if state is valid)
        """
        errors = []
        
        # Check required fields
        required_fields = ["service_name", "country", "session_id"]
        for field in required_fields:
            if not state.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Check status consistency
        if state["clarification_status"] == ProcessingStatus.COMPLETED and not state.get("clarified_requirements"):
            errors.append("Clarification marked complete but no clarified_requirements found")
        
        if state["description_status"] == ProcessingStatus.COMPLETED and not state.get("service_description"):
            errors.append("Description marked complete but no service_description found")
        
        if state["search_status"] == ProcessingStatus.COMPLETED and not state.get("vendor_results"):
            errors.append("Search marked complete but no vendor_results found")
        
        if state["report_status"] == ProcessingStatus.COMPLETED and not state.get("final_report"):
            errors.append("Report marked complete but no final_report found")
        
        # Check retry limits
        if state.get("retry_count", 0) > state.get("max_retries", 3):
            errors.append("Retry count exceeds maximum allowed retries")
        
        return errors
    
    def get_workflow_summary(self, state: ProcurementState) -> Dict[str, Any]:
        """
        Get a summary of the current workflow state.
        
        Args:
            state: Current procurement state
            
        Returns:
            Dictionary containing workflow summary
        """
        return {
            "session_id": state["session_id"],
            "service_name": state["service_name"],
            "country": state["country"],
            "status": {
                "clarification": state["clarification_status"].value,
                "description": state["description_status"].value,
                "search": state["search_status"].value,
                "report": state["report_status"].value
            },
            "progress": {
                "completed_steps": sum(1 for status in [
                    state["clarification_status"],
                    state["description_status"],
                    state["search_status"],
                    state["report_status"]
                ] if status == ProcessingStatus.COMPLETED),
                "total_steps": 4,
                "percentage": sum(1 for status in [
                    state["clarification_status"],
                    state["description_status"],
                    state["search_status"],
                    state["report_status"]
                ] if status == ProcessingStatus.COMPLETED) / 4 * 100
            },
            "next_step": self.determine_next_step(state),
            "is_complete": self.is_workflow_complete(state),
            "has_failed": self.has_workflow_failed(state),
            "retry_count": state.get("retry_count", 0),
            "errors": state.get("errors", []),
            "warnings": state.get("warnings", []),
            "start_time": state["start_time"].isoformat() if state.get("start_time") else None,
            "processing_time": self._calculate_processing_time(state)
        }
    
    def _calculate_processing_time(self, state: ProcurementState) -> Optional[str]:
        """Calculate total processing time."""
        try:
            start_time = state.get("start_time")
            if start_time:
                duration = datetime.now() - start_time
                return f"{duration.total_seconds():.2f} seconds"
        except:
            pass
        return None


def create_workflow_orchestrator() -> WorkflowOrchestrator:
    """Factory function to create a workflow orchestrator instance."""
    return WorkflowOrchestrator()
