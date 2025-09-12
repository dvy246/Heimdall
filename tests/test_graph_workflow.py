"""Tests for LangGraph workflow and state management."""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, AsyncMock, patch
from src.graph.state import HeimdallState
from langchain_core.messages import HumanMessage, AIMessage


class TestHeimdallState:
    """Test suite for Heimdall state management."""

    def test_state_initialization(self) -> None:
        """Test basic state initialization."""
        state = HeimdallState(
            ticker="AAPL",
            company_name="Apple Inc.",
            messages=[HumanMessage(content="Test message")]
        )
        
        assert state["ticker"] == "AAPL"
        assert state["company_name"] == "Apple Inc."
        assert len(state["messages"]) == 1

    def test_state_optional_fields(self) -> None:
        """Test that optional fields can be None."""
        state = HeimdallState(
            ticker="MSFT",
            company_name="Microsoft Corporation",
            messages=[]
        )
        
        # Optional fields should be accessible but None by default
        assert state.get("financial_report") is None
        assert state.get("valuation_report") is None
        assert state.get("final_report") is None

    def test_state_update(self) -> None:
        """Test state updates during workflow."""
        state = HeimdallState(
            ticker="GOOGL",
            company_name="Alphabet Inc.",
            messages=[]
        )
        
        # Simulate workflow updates
        state["mission_plan"] = "Analyze Alphabet's AI strategy"
        state["financial_report"] = "Strong revenue growth in cloud segment"
        
        assert state["mission_plan"] == "Analyze Alphabet's AI strategy"
        assert state["financial_report"] == "Strong revenue growth in cloud segment"


class TestWorkflowIntegration:
    """Test suite for workflow integration."""

    @pytest.mark.asyncio
    async def test_workflow_creation(self) -> None:
        """Test workflow graph creation."""
        try:
            from src.graph import graph
            
            # Test that workflow graph exists and is compiled
            if graph is None:
                pytest.skip("Workflow graph not available due to missing dependencies")
            
            assert graph is not None
            assert hasattr(graph, 'invoke')
            
        except ImportError:
            pytest.skip("Workflow module not implemented yet")

    def test_message_handling(self) -> None:
        """Test message addition and management."""
        initial_messages = [HumanMessage(content="Start analysis")]
        
        state = HeimdallState(
            ticker="TSLA",
            company_name="Tesla Inc.",
            messages=initial_messages
        )
        
        # Add AI response
        state["messages"].append(AIMessage(content="Analysis started"))
        
        assert len(state["messages"]) == 2
        assert isinstance(state["messages"][0], HumanMessage)
        assert isinstance(state["messages"][1], AIMessage)


class TestWorkflowValidation:
    """Test suite for workflow validation logic."""

    def test_required_fields_validation(self) -> None:
        """Test validation of required state fields."""
        try:
            from src.graph.state import HeimdallState
            
            # Test creating state with all required fields works
            state = HeimdallState(
                ticker="AAPL",
                company_name="Apple Inc.",
                messages=[]
            )
            assert state["ticker"] == "AAPL"
            assert state["company_name"] == "Apple Inc."
            
        except ImportError:
            pytest.skip("HeimdallState not available")

    def test_state_completeness_check(self) -> None:
        """Test checking if state has all required reports."""
        state = HeimdallState(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            messages=[]
        )
        
        # Helper function to check if analysis is complete
        def is_analysis_complete(state: HeimdallState) -> bool:
            required_reports = [
                "financial_report",
                "research_report", 
                "risk_report",
                "valuation_report"
            ]
            return all(state.get(field) is not None for field in required_reports)
        
        assert not is_analysis_complete(state)
        
        # Add reports
        state["financial_report"] = "Financial analysis complete"
        state["research_report"] = "Research analysis complete"
        state["risk_report"] = "Risk analysis complete"
        state["valuation_report"] = "Valuation analysis complete"
        
        assert is_analysis_complete(state)
