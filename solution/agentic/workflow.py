"""
Multi-Agent Workflow using LangGraph

This module implements the main workflow that orchestrates:
- Agent coordination and routing
- State management
- Message passing between agents
- Response synthesis
"""

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import Dict, List, Any, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import os
from datetime import datetime

# Import agents
from .agents import (
    SupervisorAgent,
    KnowledgeBaseAgent,
    TechnicalSupportAgent,
    BillingAgent,
    AccountManagementAgent,
    RAGAgent
)

# Import tools
from .tools import DatabaseTool, SearchTool, ActionTool
from .ticket_router import TicketRouter
from .knowledge_retrieval import KnowledgeRetrievalSystem
from .tools.support_operations import SupportOperationTools
from .memory import ConversationMemoryManager
from .memory_enhanced import EnhancedMemoryManager
from .workflow_logger import WorkflowLogger, TicketStage

# Define state structure
class AgentState(TypedDict):
    messages: Annotated[List[Any], add_messages]
    current_agent: str
    agent_responses: List[Dict[str, Any]]
    user_context: Dict[str, Any]
    intent: Dict[str, Any]
    final_response: str
    escalation_required: bool
    conversation_id: str

class MultiAgentWorkflow:
    def __init__(self, knowledge_base_data: List[Dict[str, Any]], db_paths: Dict[str, str]):
        """
        Initialize the multi-agent workflow
        
        Args:
            knowledge_base_data: List of knowledge base articles
            db_paths: Dictionary with 'core' and 'external' database paths
        """
        self.knowledge_base_data = knowledge_base_data
        self.db_paths = db_paths
        
        # Initialize LLM with Vocareum configuration
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY", "dummy-key"),
            base_url="https://openai.vocareum.com/v1"
        )
        
        # Initialize tools
        self.database_tool = DatabaseTool(
            core_db_path=db_paths["core"],
            external_db_path=db_paths["external"]
        )
        self.search_tool = SearchTool(knowledge_base_data)
        self.action_tool = ActionTool(self.database_tool)
        
        # Initialize ticket router
        self.ticket_router = TicketRouter()
        
        # Initialize knowledge retrieval system
        self.knowledge_retrieval = KnowledgeRetrievalSystem(knowledge_base_data)
        
        # Initialize support operation tools
        self.support_tools = SupportOperationTools(
            cultpass_db_path=db_paths["external"],
            udahub_db_path=db_paths["core"]
        )
        
        # Initialize persistent memory manager
        self.memory = ConversationMemoryManager(db_paths["core"])
        
        # Initialize enhanced memory manager
        self.enhanced_memory = EnhancedMemoryManager(db_paths["core"])
        
        # Initialize workflow logger
        self.logger = WorkflowLogger("logs/workflow_logs.jsonl")
        
        # Initialize agents
        self.supervisor = SupervisorAgent(self.llm)
        self.knowledge_base_agent = KnowledgeBaseAgent(self.llm, knowledge_base_data)
        self.technical_agent = TechnicalSupportAgent(self.llm, self.knowledge_base_agent)
        self.billing_agent = BillingAgent(self.llm, self.knowledge_base_agent)
        self.account_agent = AccountManagementAgent(self.llm, self.knowledge_base_agent)
        self.rag_agent = RAGAgent(self.llm, knowledge_base_data)
        
        # Create workflow graph
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the main workflow graph"""
        
        # Create workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("knowledge_base", self._knowledge_base_node)
        workflow.add_node("technical", self._technical_node)
        workflow.add_node("billing", self._billing_node)
        workflow.add_node("account", self._account_node)
        workflow.add_node("rag", self._rag_node)
        workflow.add_node("multi_agent", self._multi_agent_node)
        workflow.add_node("escalation", self._escalation_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # Add conditional edges from supervisor to specialist agents
        workflow.add_conditional_edges(
            "supervisor",
            self._route_decision,
            {
                "knowledge_base": "knowledge_base",
                "technical": "technical",
                "billing": "billing",
                "account": "account",
                "rag": "rag",
                "multi_agent": "multi_agent",
                "escalation": "escalation"
            }
        )
        
        # Add edges from specialist agents to synthesis
        workflow.add_edge("knowledge_base", "synthesize")
        workflow.add_edge("technical", "synthesize")
        workflow.add_edge("billing", "synthesize")
        workflow.add_edge("account", "synthesize")
        workflow.add_edge("rag", "synthesize")
        workflow.add_edge("multi_agent", "synthesize")
        workflow.add_edge("escalation", END)
        
        # Add edge from synthesis to end
        workflow.add_edge("synthesize", END)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        return workflow.compile()
    
    def _supervisor_node(self, state: AgentState) -> AgentState:
        """Supervisor agent node - analyze intent and prepare routing"""
        # Get the latest user message
        messages = state["messages"]
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            state["final_response"] = "I didn't receive a valid message. Please try again."
            return state
        
        # Ensure persistent conversation and load prior context
        user_id = state.get("user_context", {}).get("user_id") or "guest-user"
        conv_id = state.get("user_context", {}).get("conversation_id") or state.get("conversation_id") or None
        ticket_id = self.memory.ensure_conversation(user_id=user_id, conversation_id=conv_id)
        
        # Create or get session for enhanced memory
        thread_id = state.get("user_context", {}).get("thread_id") or f"thread-{user_id}"
        session_id = self.enhanced_memory.create_session(thread_id, user_id, conv_id or ticket_id)
        
        # Persist incoming user message
        try:
            self.memory.add_user_message(ticket_id, user_message)
            self.enhanced_memory.add_session_message(session_id, "user", user_message)
        except Exception:
            pass
        
        # Prepare historical context
        persisted_context = self.memory.prepare_context(user_id, ticket_id)
        
        # Get enhanced memory context for agent decision-making
        enhanced_context = self.enhanced_memory.get_context_for_agent(session_id, user_id)

        # Create ticket metadata for routing
        ticket_metadata = {
            "ticket_id": ticket_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "user_type": state.get("user_context", {}).get("user_type", "standard"),
            "user_blocked": state.get("user_context", {}).get("user_blocked", False),
            "previous_tickets": persisted_context.get("previous_tickets", 0)
        }
        
        # Route ticket using intelligent routing
        routing_decision = self.ticket_router.route_ticket(user_message, ticket_metadata)
        
        # Log routing decision
        self.logger.log_agent_decision("supervisor", routing_decision, routing_decision.get("confidence", 0.0))
        self.logger.log_workflow_stage(TicketStage.CLASSIFICATION)
        
        # Retrieve knowledge based on query
        knowledge_result = self.knowledge_retrieval.retrieve_knowledge(user_message, ticket_metadata)
        
        # Log knowledge retrieval
        self.logger.log_knowledge_retrieval(
            user_message,
            len(knowledge_result.articles),
            knowledge_result.confidence_level.value if hasattr(knowledge_result.confidence_level, 'value') else 0.0,
            knowledge_result.should_escalate
        )
        self.logger.log_workflow_stage(TicketStage.KNOWLEDGE_RETRIEVAL)
        
        # Analyze intent (for backward compatibility)
        intent = self.supervisor.analyze_intent(user_message, state.get("user_context"))
        
        # Update context with routing and knowledge information
        context = self.supervisor.update_context(
            state.get("user_context", {}),
            user_message,
            intent
        )
        context["routing_decision"] = routing_decision
        context["knowledge_result"] = knowledge_result
        context["support_tools"] = self.support_tools
        context["memory"] = {
            "ticket_id": ticket_id,
            "history_preview": persisted_context.get("history_preview", ""),
            "previous_interactions": persisted_context.get("previous_interactions_count", 0),
            "last_interaction_at": persisted_context.get("last_interaction_at"),
        }
        
        # Add enhanced memory context
        context["enhanced_memory"] = {
            "session_id": session_id,
            "thread_id": thread_id,
            "state_memory": enhanced_context.get("state", {}),
            "session_memory": enhanced_context.get("session", {}),
            "long_term_memory": enhanced_context.get("long_term", {}),
            "conversation_history": enhanced_context.get("conversation_history", [])
        }
        
        # Use knowledge result for escalation if no relevant knowledge found
        escalation_required = routing_decision.get("requires_escalation", False) or knowledge_result.should_escalate
        
        # Log escalation if required
        if escalation_required:
            self.logger.log_escalation(
                "Low confidence or complex issue",
                "automatic",
                {"routing_confidence": routing_decision.get("confidence", 0.0), "knowledge_confidence": knowledge_result.confidence_level.value if hasattr(knowledge_result.confidence_level, 'value') else 0.0}
            )
            self.logger.log_workflow_stage(TicketStage.ESCALATION)
        
        # Update state
        state["intent"] = intent
        state["user_context"] = context
        state["escalation_required"] = escalation_required
        state["routing_decision"] = routing_decision
        state["current_agent"] = "supervisor"
        
        return state
    
    def _route_decision(self, state: AgentState) -> str:
        """Decide which agent to route to based on routing decision"""
        routing_decision = state.get("routing_decision", {})
        escalation_required = state.get("escalation_required", False)
        
        if escalation_required:
            self.logger.log_routing_choice("supervisor", "escalation", "Escalation required")
            self.logger.log_workflow_stage(TicketStage.ROUTING)
            return "escalation"
        
        # Use routing decision for agent selection
        recommended_agents = routing_decision.get("recommended_agents", ["KNOWLEDGE_BASE"])
        category = routing_decision.get("category", "general")
        complexity = routing_decision.get("complexity", "moderate")
        
        # For complex tickets, use multi-agent approach
        if complexity == "complex" and len(recommended_agents) > 1:
            self.logger.log_routing_choice("supervisor", "multi_agent", f"Complex ticket requiring multiple agents")
            self.logger.log_workflow_stage(TicketStage.ROUTING)
            return "multi_agent"
        
        # Map category to agent
        category_agent_map = {
            "technical": "technical",
            "billing": "billing", 
            "account": "account",
            "general": "knowledge_base",
            "escalation": "escalation"
        }
        
        target_agent = category_agent_map.get(category, "knowledge_base")
        self.logger.log_routing_choice("supervisor", target_agent, f"Category: {category}, Complexity: {complexity}")
        self.logger.log_workflow_stage(TicketStage.ROUTING)
        
        return target_agent
    
    def _knowledge_base_node(self, state: AgentState) -> AgentState:
        """Knowledge base agent node"""
        messages = state["messages"]
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            return state
        
        # Process query with knowledge base agent
        response = self.knowledge_base_agent.process_query(user_message, state.get("user_context"))
        
        # Log agent decision and resolution attempt
        self.logger.log_agent_decision("knowledge_base", response, response.get("confidence", 0.0))
        self.logger.log_resolution_attempt("knowledge_base", "knowledge_retrieval", True, {
            "articles_used": response.get("articles_used", []),
            "confidence": response.get("confidence", 0.0)
        })
        self.logger.log_workflow_stage(TicketStage.RESOLUTION_ATTEMPT)
        
        # Add response to state
        agent_responses = state.get("agent_responses", [])
        agent_responses.append(response)
        
        state["agent_responses"] = agent_responses
        state["current_agent"] = "knowledge_base"
        
        return state
    
    def _technical_node(self, state: AgentState) -> AgentState:
        """Technical support agent node"""
        messages = state["messages"]
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            return state
        
        # Process query with technical agent
        response = self.technical_agent.process_query(user_message, state.get("user_context"))
        
        # Add response to state
        agent_responses = state.get("agent_responses", [])
        agent_responses.append(response)
        
        state["agent_responses"] = agent_responses
        state["current_agent"] = "technical"
        
        return state
    
    def _billing_node(self, state: AgentState) -> AgentState:
        """Billing agent node"""
        messages = state["messages"]
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            return state
        
        # Process query with billing agent
        response = self.billing_agent.process_query(user_message, state.get("user_context"))
        
        # Add response to state
        agent_responses = state.get("agent_responses", [])
        agent_responses.append(response)
        
        state["agent_responses"] = agent_responses
        state["current_agent"] = "billing"
        
        return state
    
    def _account_node(self, state: AgentState) -> AgentState:
        """Account management agent node"""
        messages = state["messages"]
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            return state
        
        # Process query with account agent
        response = self.account_agent.process_query(user_message, state.get("user_context"))
        
        # Add response to state
        agent_responses = state.get("agent_responses", [])
        agent_responses.append(response)
        
        state["agent_responses"] = agent_responses
        state["current_agent"] = "account"
        
        return state
    
    def _rag_node(self, state: AgentState) -> AgentState:
        """RAG agent node"""
        messages = state["messages"]
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            return state
        
        # Process query with RAG agent
        response = self.rag_agent.process_query(user_message, state.get("user_context"))
        
        # Add response to state
        agent_responses = state.get("agent_responses", [])
        agent_responses.append(response)
        
        state["agent_responses"] = agent_responses
        state["current_agent"] = "rag"
        
        return state
    
    def _multi_agent_node(self, state: AgentState) -> AgentState:
        """Multi-agent consultation node"""
        messages = state["messages"]
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            return state
        
        # Get responses from multiple agents
        agent_responses = []
        
        # Knowledge base response
        kb_response = self.knowledge_base_agent.process_query(user_message, state.get("user_context"))
        agent_responses.append(kb_response)
        
        # RAG response
        rag_response = self.rag_agent.process_query(user_message, state.get("user_context"))
        agent_responses.append(rag_response)
        
        # Technical response (if relevant)
        if any(word in user_message.lower() for word in ["login", "password", "error", "bug"]):
            tech_response = self.technical_agent.process_query(user_message, state.get("user_context"))
            agent_responses.append(tech_response)
        
        # Billing response (if relevant)
        if any(word in user_message.lower() for word in ["payment", "subscription", "billing", "refund"]):
            billing_response = self.billing_agent.process_query(user_message, state.get("user_context"))
            agent_responses.append(billing_response)
        
        state["agent_responses"] = agent_responses
        state["current_agent"] = "multi_agent"
        
        return state
    
    def _escalation_node(self, state: AgentState) -> AgentState:
        """Escalation node - handle human escalation"""
        messages = state["messages"]
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        escalation_response = {
            "agent": "ESCALATION",
            "response": "I understand this is a complex issue that requires human assistance. I'm escalating this to our support team who will contact you shortly. In the meantime, I've logged your query and our team will review it as soon as possible.",
            "escalation_reason": "Complex query requiring human intervention",
            "estimated_response_time": "2-4 hours"
        }
        
        state["agent_responses"] = [escalation_response]
        state["current_agent"] = "escalation"
        state["final_response"] = escalation_response["response"]
        
        return state
    
    def _synthesize_node(self, state: AgentState) -> AgentState:
        """Synthesize responses from agents"""
        agent_responses = state.get("agent_responses", [])
        messages = state["messages"]
        
        # Get original user message
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not agent_responses:
            state["final_response"] = "I apologize, but I couldn't process your request. Please try rephrasing your question."
            return state
        
        if len(agent_responses) == 1:
            # Single agent response
            state["final_response"] = agent_responses[0].get("response", "No response available")
        else:
            # Multi-agent response synthesis
            state["final_response"] = self.supervisor.synthesize_response(agent_responses, user_message)

        # Persist AI response in memory if we have a ticket
        try:
            mem = state.get("user_context", {}).get("memory", {})
            ticket_id = mem.get("ticket_id")
            if ticket_id and state.get("final_response"):
                self.memory.add_ai_message(ticket_id, state["final_response"])
            
            # Update enhanced memory
            enhanced_mem = state.get("user_context", {}).get("enhanced_memory", {})
            session_id = enhanced_mem.get("session_id")
            user_id = state.get("user_context", {}).get("user_id") or "guest-user"
            
            if session_id and state.get("final_response"):
                self.enhanced_memory.add_session_message(session_id, "ai", state["final_response"])
                
                # Update agent context with decision
                agent_responses = state.get("agent_responses", [])
                if agent_responses:
                    last_agent_response = agent_responses[-1]
                    self.enhanced_memory.update_agent_context(session_id, user_id, last_agent_response)
        except Exception:
            pass
        
        return state
    
    def process_query(self, query: str, user_id: str = None, conversation_id: str = None) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent workflow
        
        Args:
            query: User's query
            user_id: User ID for context
            conversation_id: Conversation ID for tracking
            
        Returns:
            Dictionary containing the response and metadata
        """
        # Generate ticket ID if not provided
        ticket_id = conversation_id or f"ticket_{uuid.uuid4().hex[:8]}"
        user_id = user_id or "guest-user"
        
        # Start logging session
        self.logger.start_ticket_session(ticket_id, user_id, query)
        self.logger.log_workflow_stage(TicketStage.SUBMISSION)
        
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "current_agent": "",
            "agent_responses": [],
            "user_context": {
                "user_id": user_id,
                "conversation_id": ticket_id,
                "message_count": 1
            },
            "intent": {},
            "final_response": "",
            "escalation_required": False,
            "conversation_id": ticket_id
        }
        
        # Execute workflow
        try:
            result = self.workflow.invoke(initial_state)
            
            # Log completion
            final_status = "escalated" if result.get("escalation_required", False) else "resolved"
            resolution_summary = f"Processed by {len(result.get('agent_responses', []))} agents"
            self.logger.log_ticket_completion(final_status, resolution_summary, 0.0)
            
            return {
                "response": result["final_response"],
                "agents_used": [resp.get("agent") for resp in result.get("agent_responses", [])],
                "intent": result.get("intent", {}),
                "escalation_required": result.get("escalation_required", False),
                "conversation_id": result.get("conversation_id"),
                "agent_responses": result.get("agent_responses", []),
                "user_context": result.get("user_context", {}),
                "ticket_id": ticket_id
            }
        
        except Exception as e:
            # Log error
            self.logger.log_error("workflow_execution", str(e), {"query": query, "user_id": user_id})
            self.logger.log_ticket_completion("error", f"Error: {str(e)}", 0.0)
            
            return {
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again or contact support.",
                "error": str(e),
                "agents_used": [],
                "escalation_required": True,
                "ticket_id": ticket_id
            }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow and available agents"""
        return {
            "workflow_type": "Multi-Agent Supervisor Pattern",
            "agents": [
                "Supervisor Agent",
                "Knowledge Base Agent", 
                "Technical Support Agent",
                "Billing Agent",
                "Account Management Agent",
                "RAG Agent"
            ],
            "tools": [
                "Database Tool",
                "Search Tool",
                "Action Tool"
            ],
            "capabilities": [
                "Intent analysis and routing",
                "Multi-agent coordination",
                "Response synthesis",
                "Escalation handling",
                "Context management"
            ]
        }