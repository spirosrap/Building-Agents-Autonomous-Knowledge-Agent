"""
Supervisor Agent - Central Coordinator and Decision Maker

This agent is responsible for:
- Analyzing incoming user queries and determining intent
- Routing requests to appropriate specialist agents
- Coordinating multi-agent conversations
- Maintaining conversation context and state
- Making final decisions on responses
- Handling escalation to human agents when needed
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import re

class SupervisorAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the supervisor agent"""
        return """You are the Supervisor Agent for Uda-hub, a customer support system for CultPass users. Your role is to:

1. ANALYZE user queries to determine intent and complexity
2. ROUTE requests to appropriate specialist agents
3. COORDINATE multi-agent conversations
4. SYNTHESIZE responses from multiple agents
5. MAINTAIN conversation context and state

Available specialist agents:
- KNOWLEDGE_BASE: For general support questions, FAQ, how-to guides
- TECHNICAL: For login issues, app problems, technical troubleshooting
- BILLING: For subscription, payment, refund, pricing questions
- ACCOUNT: For account management, preferences, transfers, privacy
- RAG: For complex queries requiring semantic search and generation

Intent classification keywords:
- KNOWLEDGE_BASE: "how to", "what is", "guide", "help", "information", "article"
- TECHNICAL: "login", "password", "error", "bug", "crash", "not working", "technical"
- BILLING: "payment", "subscription", "billing", "refund", "charge", "cost", "premium"
- ACCOUNT: "account", "profile", "preferences", "settings", "transfer", "privacy"
- RAG: "complex", "detailed", "comprehensive", "multiple", "advanced"

Respond with a JSON object containing:
{
    "intent": "KNOWLEDGE_BASE|TECHNICAL|BILLING|ACCOUNT|RAG|ESCALATION",
    "confidence": 0.0-1.0,
    "complexity": "SIMPLE|COMPLEX",
    "required_agents": ["agent1", "agent2"],
    "reasoning": "explanation of your decision"
}"""

    def analyze_intent(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze user intent and determine routing with enhanced memory context"""
        
        # Build enhanced prompt with memory context
        enhanced_prompt = self.system_prompt
        
        if context and context.get("enhanced_memory"):
            enhanced_prompt += "\n\nMEMORY CONTEXT:\n"
            enhanced_memory = context["enhanced_memory"]
            
            # Add session information
            session = enhanced_memory.get("session_memory", {})
            if session:
                enhanced_prompt += f"- Current session step: {session.get('current_step', 0)}\n"
                enhanced_prompt += f"- Session duration: {session.get('session_duration', 0):.1f} seconds\n"
                enhanced_prompt += f"- Messages in session: {session.get('message_count', 0)}\n"
            
            # Add state memory
            state_memory = enhanced_memory.get("state_memory", {})
            if state_memory:
                enhanced_prompt += "- Current state:\n"
                for key, data in state_memory.items():
                    enhanced_prompt += f"  * {key}: {data.get('value')}\n"
            
            # Add long-term memory
            long_term = enhanced_memory.get("long_term_memory", {})
            if long_term:
                enhanced_prompt += "- Previous interactions:\n"
                for key, data in long_term.items():
                    enhanced_prompt += f"  * {key}: {data.get('value')}\n"
            
            # Add conversation history
            history = enhanced_memory.get("conversation_history", [])
            if history:
                enhanced_prompt += "- Recent conversation history:\n"
                for conv in history[:2]:  # Last 2 conversations
                    enhanced_prompt += f"  * Conversation {conv.get('ticket_id', 'unknown')}:\n"
                    for msg in conv.get("messages", [])[-3:]:  # Last 3 messages
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")[:100]
                        enhanced_prompt += f"    {role}: {content}...\n"
        
        messages = [
            SystemMessage(content=enhanced_prompt),
            HumanMessage(content=f"Analyze this user query: '{query}'")
        ]
        
        response = self.llm.invoke(messages)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group())
                return intent_data
            else:
                # Fallback analysis
                return self._fallback_intent_analysis(query)
        except json.JSONDecodeError:
            return self._fallback_intent_analysis(query)
    
    def _fallback_intent_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback intent analysis using keyword matching"""
        query_lower = query.lower()
        
        # Keyword-based classification
        if any(word in query_lower for word in ["login", "password", "error", "bug", "crash", "not working"]):
            return {
                "intent": "TECHNICAL",
                "confidence": 0.8,
                "complexity": "SIMPLE",
                "required_agents": ["TECHNICAL"],
                "reasoning": "Query contains technical keywords"
            }
        elif any(word in query_lower for word in ["payment", "subscription", "billing", "refund", "charge", "cost"]):
            return {
                "intent": "BILLING",
                "confidence": 0.8,
                "complexity": "SIMPLE",
                "required_agents": ["BILLING"],
                "reasoning": "Query contains billing keywords"
            }
        elif any(word in query_lower for word in ["account", "profile", "preferences", "settings", "transfer"]):
            return {
                "intent": "ACCOUNT",
                "confidence": 0.8,
                "complexity": "SIMPLE",
                "required_agents": ["ACCOUNT"],
                "reasoning": "Query contains account management keywords"
            }
        else:
            return {
                "intent": "KNOWLEDGE_BASE",
                "confidence": 0.6,
                "complexity": "SIMPLE",
                "required_agents": ["KNOWLEDGE_BASE"],
                "reasoning": "Default to knowledge base for general queries"
            }
    
    def route_query(self, intent: Dict[str, Any]) -> str:
        """Route query to appropriate specialist agent(s)"""
        intent_type = intent.get("intent", "KNOWLEDGE_BASE")
        complexity = intent.get("complexity", "SIMPLE")
        
        if complexity == "COMPLEX" or intent_type == "RAG":
            return "MULTI_AGENT"
        elif intent_type == "ESCALATION":
            return "ESCALATION"
        else:
            return intent_type
    
    def synthesize_response(self, agent_responses: List[Dict[str, Any]], original_query: str) -> str:
        """Synthesize responses from multiple agents"""
        if not agent_responses:
            return "I apologize, but I couldn't get a proper response from our specialist agents. Please try rephrasing your question."
        
        if len(agent_responses) == 1:
            return agent_responses[0].get("response", "No response available")
        
        # Multi-agent response synthesis
        synthesis_prompt = f"""Synthesize the following agent responses into a coherent, helpful answer for the user query: "{original_query}"

Agent Responses:
"""
        
        for i, agent_response in enumerate(agent_responses, 1):
            synthesis_prompt += f"\n{i}. {agent_response.get('agent', 'Unknown')}: {agent_response.get('response', 'No response')}"
        
        synthesis_prompt += "\n\nProvide a comprehensive, well-structured response that addresses all aspects of the user's query."
        
        messages = [
            SystemMessage(content="You are a response synthesis expert. Combine multiple agent responses into a single, coherent, and helpful response."),
            HumanMessage(content=synthesis_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def should_escalate(self, query: str, context: Dict[str, Any] = None) -> bool:
        """Determine if query should be escalated to human agent"""
        escalation_keywords = [
            "human", "person", "real", "agent", "representative", "speak to someone",
            "urgent", "emergency", "critical", "complaint", "dispute", "legal"
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in escalation_keywords):
            return True
        
        # Check conversation length
        if context and context.get("message_count", 0) > 10:
            return True
        
        return False
    
    def update_context(self, context: Dict[str, Any], query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation context"""
        if context is None:
            context = {}
        
        context["last_query"] = query
        context["last_intent"] = intent
        context["message_count"] = context.get("message_count", 0) + 1
        context["conversation_history"] = context.get("conversation_history", [])
        context["conversation_history"].append({
            "query": query,
            "intent": intent,
            "timestamp": "now"  # In real implementation, use actual timestamp
        })
        
        return context
