"""
Multi-Agent System for Uda-hub Customer Support

This package contains the specialized agents for the multi-agent architecture:
- Supervisor Agent: Central coordinator and decision maker
- Knowledge Base Agent: Expert in retrieving support information
- Technical Support Agent: Expert in technical issues and troubleshooting
- Billing Agent: Expert in payment and subscription matters
- Account Management Agent: Expert in user account operations
- RAG Agent: Retrieval-Augmented Generation specialist
"""

from .supervisor import SupervisorAgent
from .knowledge_base import KnowledgeBaseAgent
from .technical import TechnicalSupportAgent
from .billing import BillingAgent
from .account import AccountManagementAgent
from .rag import RAGAgent

__all__ = [
    "SupervisorAgent",
    "KnowledgeBaseAgent", 
    "TechnicalSupportAgent",
    "BillingAgent",
    "AccountManagementAgent",
    "RAGAgent"
]
