"""
LangGraph workflow implementation for the Procurement Discovery Tool.

This module defines the complete workflow using LangGraph's StateGraph,
connecting all agents in a coordinated procurement discovery process.
"""

from typing import Dict, Any, List, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

from ..models.state import ProcurementState, ProcessingStatus
from ..agents.clarification_agent import create_clarification_agent
from ..agents.description_agent import create_description_agent
from ..agents.search_agent import create_search_agent
from ..agents.report_agent import create_report_generation_agent
from ..agents.orchestrator import create_workflow_orchestrator
from ..config.settings import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ProcurementWorkflow:
    """Main workflow class for procurement discovery using LangGraph."""
    
    def __init__(self):
        """Initialize the procurement workflow."""
        # Initialize agents
        self.clarification_agent = create_clarification_agent()
        self.description_agent = create_description_agent()
        self.search_agent = create_search_agent()
        self.report_agent = create_report_generation_agent()
        self.orchestrator = create_workflow_orchestrator()
        
        # Initialize checkpointer for state persistence
        self.checkpointer = MemorySaver() if config.workflow.enable_state_persistence else None
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        logger.info("Procurement workflow initialized successfully")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create a new StateGraph with our ProcurementState type
        workflow = StateGraph(ProcurementState)
        
        # Add nodes for each agent
        workflow.add_node("clarification", self._clarification_node)
        workflow.add_node("description", self._description_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("report", self._report_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("clarification")
        
        # Add conditional edges based on processing status
        workflow.add_conditional_edges(
            "clarification",
            self._route_after_clarification,
            {
                "description": "description",
                "error": "error_handler",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "description", 
            self._route_after_description,
            {
                "search": "search",
                "error": "error_handler",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "search",
            self._route_after_search,
            {
                "report": "report",
                "error": "error_handler", 
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "report",
            self._route_after_report,
            {
                "end": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "error_handler",
            self._route_after_error,
            {
                "clarification": "clarification",
                "description": "description", 
                "search": "search",
                "report": "report",
                "end": END
            }
        )
        
        # Compile the workflow
        compiled_workflow = workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("Workflow graph compiled successfully")
        return compiled_workflow
    
    # Node implementations
    def _clarification_node(self, state: ProcurementState) -> ProcurementState:
        """Execute the clarification agent."""
        logger.info(f"Executing clarification node for session {state['session_id']}")
        
        try:
            updated_state = self.clarification_agent.process(state)
            return updated_state
        except Exception as e:
            logger.error(f"Error in clarification node: {str(e)}")
            state["clarification_status"] = ProcessingStatus.FAILED
            state["errors"].append(f"Clarification node failed: {str(e)}")
            return state
    
    def _description_node(self, state: ProcurementState) -> ProcurementState:
        """Execute the description agent."""
        logger.info(f"Executing description node for session {state['session_id']}")
        
        try:
            updated_state = self.description_agent.process(state)
            return updated_state
        except Exception as e:
            logger.error(f"Error in description node: {str(e)}")
            state["description_status"] = ProcessingStatus.FAILED
            state["errors"].append(f"Description node failed: {str(e)}")
            return state
    
    def _search_node(self, state: ProcurementState) -> ProcurementState:
        """Execute the search agent."""
        logger.info(f"Executing search node for session {state['session_id']}")
        
        try:
            updated_state = self.search_agent.process(state)
            return updated_state
        except Exception as e:
            logger.error(f"Error in search node: {str(e)}")
            state["search_status"] = ProcessingStatus.FAILED
            state["errors"].append(f"Search node failed: {str(e)}")
            return state
    
    def _report_node(self, state: ProcurementState) -> ProcurementState:
        """Execute the report generation agent."""
        logger.info(f"Executing report node for session {state['session_id']}")
        
        try:
            updated_state = self.report_agent.process(state)
            return updated_state
        except Exception as e:
            logger.error(f"Error in report node: {str(e)}")
            state["report_status"] = ProcessingStatus.FAILED
            state["errors"].append(f"Report node failed: {str(e)}")
            return state
    
    def _error_handler_node(self, state: ProcurementState) -> ProcurementState:
        """Handle errors and determine retry strategy."""
        logger.info(f"Executing error handler for session {state['session_id']}")
        
        # Increment retry count
        state["retry_count"] = state.get("retry_count", 0) + 1
        
        # Log error details
        logger.warning(f"Error handling - Retry count: {state['retry_count']}, Errors: {state['errors']}")
        
        # Add error handling timestamp
        state["timestamps"][f"error_handled_{state['retry_count']}"] = datetime.now()
        
        return state
    
    # Routing functions
    def _route_after_clarification(self, state: ProcurementState) -> Literal["description", "error", "end"]:
        """Route after clarification step."""
        if state["clarification_status"] == ProcessingStatus.COMPLETED:
            return "description"
        elif state["clarification_status"] == ProcessingStatus.FAILED:
            if self.clarification_agent.should_retry(state):
                return "error"
            else:
                return "end"
        return "end"
    
    def _route_after_description(self, state: ProcurementState) -> Literal["search", "error", "end"]:
        """Route after description step."""
        if state["description_status"] == ProcessingStatus.COMPLETED:
            return "search"
        elif state["description_status"] == ProcessingStatus.FAILED:
            if self.description_agent.should_retry(state):
                return "error"
            else:
                return "end"
        return "end"
    
    def _route_after_search(self, state: ProcurementState) -> Literal["report", "error", "end"]:
        """Route after search step."""
        if state["search_status"] == ProcessingStatus.COMPLETED:
            return "report"
        elif state["search_status"] == ProcessingStatus.FAILED:
            if self.search_agent.should_retry(state):
                return "error"
            else:
                return "end"
        return "end"
    
    def _route_after_report(self, state: ProcurementState) -> Literal["end", "error"]:
        """Route after report generation step."""
        if state["report_status"] == ProcessingStatus.COMPLETED:
            return "end"
        elif state["report_status"] == ProcessingStatus.FAILED:
            if self.report_agent.should_retry(state):
                return "error"
        return "end"
    
    def _route_after_error(self, state: ProcurementState) -> Literal["clarification", "description", "search", "report", "end"]:
        """Route after error handling."""
        # Check retry limits
        if state.get("retry_count", 0) >= state.get("max_retries", 3):
            logger.error(f"Maximum retries exceeded for session {state['session_id']}")
            return "end"
        
        # Determine which step to retry based on failure status
        if state["clarification_status"] == ProcessingStatus.FAILED:
            state["clarification_status"] = ProcessingStatus.PENDING
            return "clarification"
        elif state["description_status"] == ProcessingStatus.FAILED:
            state["description_status"] = ProcessingStatus.PENDING
            return "description"
        elif state["search_status"] == ProcessingStatus.FAILED:
            state["search_status"] = ProcessingStatus.PENDING
            return "search"
        elif state["report_status"] == ProcessingStatus.FAILED:
            state["report_status"] = ProcessingStatus.PENDING
            return "report"
        
        return "end"
    
    # Public interface methods
    def run(
        self, 
        service_name: str, 
        country: str, 
        additional_details: str = None,
        config: RunnableConfig = None
    ) -> Dict[str, Any]:
        """
        Run the complete procurement discovery workflow.
        
        Args:
            service_name: Name of service/product to discover
            country: Target country for procurement
            additional_details: Optional additional details
            config: Optional LangGraph configuration
            
        Returns:
            Dictionary containing the final results
        """
        logger.info(f"Starting procurement discovery for '{service_name}' in {country}")
        
        try:
            # Create initial state
            initial_state = self.orchestrator.create_initial_state(
                service_name=service_name,
                country=country,
                additional_details=additional_details
            )
            
            # Run the workflow
            final_state = self.workflow.invoke(
                initial_state,
                config=config or {"configurable": {"thread_id": initial_state["session_id"]}}
            )
            
            # Generate workflow summary
            summary = self.orchestrator.get_workflow_summary(final_state)
            
            # Prepare results
            results = {
                "success": self.orchestrator.is_workflow_complete(final_state),
                "session_id": final_state["session_id"],
                "summary": summary,
                "final_report": final_state.get("final_report"),
                "errors": final_state.get("errors", []),
                "warnings": final_state.get("warnings", []),
                "processing_time": summary.get("processing_time"),
                "metadata": {
                    "service_name": service_name,
                    "country": country,
                    "additional_details": additional_details,
                    "workflow_version": "1.0",
                    "completed_at": datetime.now().isoformat()
                }
            }
            
            if results["success"]:
                logger.info(f"Procurement discovery completed successfully for session {initial_state['session_id']}")
            else:
                logger.warning(f"Procurement discovery failed for session {initial_state['session_id']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "success": False,
                "session_id": None,
                "error": str(e),
                "metadata": {
                    "service_name": service_name,
                    "country": country,
                    "failed_at": datetime.now().isoformat()
                }
            }
    
    async def arun(
        self, 
        service_name: str, 
        country: str, 
        additional_details: str = None,
        config: RunnableConfig = None
    ) -> Dict[str, Any]:
        """
        Async version of the workflow execution.
        
        Args:
            service_name: Name of service/product to discover
            country: Target country for procurement
            additional_details: Optional additional details
            config: Optional LangGraph configuration
            
        Returns:
            Dictionary containing the final results
        """
        logger.info(f"Starting async procurement discovery for '{service_name}' in {country}")
        
        try:
            # Create initial state
            initial_state = self.orchestrator.create_initial_state(
                service_name=service_name,
                country=country,
                additional_details=additional_details
            )
            
            # Run the workflow asynchronously
            final_state = await self.workflow.ainvoke(
                initial_state,
                config=config or {"configurable": {"thread_id": initial_state["session_id"]}}
            )
            
            # Generate workflow summary
            summary = self.orchestrator.get_workflow_summary(final_state)
            
            # Prepare results
            results = {
                "success": self.orchestrator.is_workflow_complete(final_state),
                "session_id": final_state["session_id"],
                "summary": summary,
                "final_report": final_state.get("final_report"),
                "errors": final_state.get("errors", []),
                "warnings": final_state.get("warnings", []),
                "processing_time": summary.get("processing_time"),
                "metadata": {
                    "service_name": service_name,
                    "country": country,
                    "additional_details": additional_details,
                    "workflow_version": "1.0",
                    "completed_at": datetime.now().isoformat()
                }
            }
            
            if results["success"]:
                logger.info(f"Async procurement discovery completed successfully for session {initial_state['session_id']}")
            else:
                logger.warning(f"Async procurement discovery failed for session {initial_state['session_id']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Async workflow execution failed: {str(e)}")
            return {
                "success": False,
                "session_id": None,
                "error": str(e),
                "metadata": {
                    "service_name": service_name,
                    "country": country,
                    "failed_at": datetime.now().isoformat()
                }
            }
    
    def get_workflow_visualization(self) -> str:
        """Get a text representation of the workflow graph."""
        return """
Procurement Discovery Workflow:

┌─────────────────┐
│   START         │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Clarification  │
│     Agent       │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Description   │
│     Agent       │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│     Search      │
│     Agent       │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│     Report      │
│     Agent       │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│      END        │
└─────────────────┘

Error Handler (connected to all agents):
- Handles retries and error recovery
- Maximum 3 retry attempts per agent
- Routes back to failed agent or terminates workflow
"""


def create_procurement_workflow() -> ProcurementWorkflow:
    """Factory function to create a procurement workflow instance."""
    return ProcurementWorkflow()
