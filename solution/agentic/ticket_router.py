"""
Ticket Router - Intelligent Task Routing and Role Assignment

This module implements intelligent task routing and role assignment across agents
based on ticket characteristics, content, and metadata.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
import json
from dataclasses import dataclass
from enum import Enum

class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

class TicketCategory(Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    GENERAL = "general"
    ESCALATION = "escalation"

@dataclass
class TicketMetadata:
    """Ticket metadata for routing decisions"""
    category: TicketCategory
    priority: TicketPriority
    complexity: TicketComplexity
    urgency_score: float
    requires_escalation: bool
    estimated_resolution_time: str
    recommended_agents: List[str]
    routing_reason: str

class TicketRouter:
    """
    Intelligent ticket router that classifies and routes tickets to appropriate agents
    based on content, metadata, and routing logic.
    """
    
    def __init__(self):
        self.classification_keywords = self._create_classification_keywords()
        self.priority_keywords = self._create_priority_keywords()
        self.complexity_indicators = self._create_complexity_indicators()
    
    def _create_classification_keywords(self) -> Dict[str, List[str]]:
        """Create keywords for ticket classification"""
        return {
            "technical": [
                "login", "password", "error", "bug", "crash", "not working", "technical",
                "app", "mobile", "website", "connection", "network", "slow", "freeze",
                "qr code", "scan", "entry", "ticket", "reservation", "authentication"
            ],
            "billing": [
                "payment", "subscription", "billing", "refund", "charge", "cost", "premium",
                "monthly", "renewal", "cancel", "money", "credit", "debit", "card",
                "pricing", "fee", "charge", "invoice", "receipt"
            ],
            "account": [
                "account", "profile", "preferences", "settings", "transfer", "privacy",
                "data", "information", "update", "change", "delete", "export",
                "security", "password", "email", "personal", "details"
            ],
            "escalation": [
                "urgent", "emergency", "critical", "immediately", "human", "agent",
                "representative", "supervisor", "manager", "complaint", "dispute",
                "legal", "fraud", "unauthorized", "hacked", "compromised"
            ]
        }
    
    def _create_priority_keywords(self) -> Dict[str, List[str]]:
        """Create keywords for priority classification"""
        return {
            "urgent": ["urgent", "emergency", "critical", "immediately", "asap", "now"],
            "high": ["important", "priority", "high", "serious", "broken", "not working"],
            "medium": ["issue", "problem", "question", "help", "support"],
            "low": ["inquiry", "information", "general", "curious", "wondering"]
        }
    
    def _create_complexity_indicators(self) -> Dict[str, List[str]]:
        """Create indicators for complexity assessment"""
        return {
            "complex": [
                "multiple", "several", "various", "different", "complex", "complicated",
                "detailed", "comprehensive", "extensive", "thorough", "multiple issues",
                "combination", "related", "connected", "interdependent"
            ],
            "moderate": [
                "issue", "problem", "trouble", "difficulty", "challenge", "specific",
                "particular", "certain", "one", "single", "individual"
            ],
            "simple": [
                "simple", "basic", "quick", "easy", "straightforward", "just",
                "only", "merely", "simple question", "quick question"
            ]
        }
    
    def classify_ticket(self, ticket_content: str, metadata: Dict[str, Any] = None) -> TicketMetadata:
        """
        Classify a ticket based on content and metadata
        
        Args:
            ticket_content: The ticket description/content
            metadata: Additional ticket metadata (date, user info, etc.)
            
        Returns:
            TicketMetadata with classification results
        """
        content_lower = ticket_content.lower()
        
        # Determine category
        category = self._determine_category(content_lower)
        
        # Determine priority
        priority = self._determine_priority(content_lower, metadata)
        
        # Determine complexity
        complexity = self._determine_complexity(content_lower)
        
        # Calculate urgency score
        urgency_score = self._calculate_urgency_score(content_lower, priority, metadata)
        
        # Check if escalation is required
        requires_escalation = self._check_escalation_required(content_lower, priority, urgency_score)
        
        # Estimate resolution time
        resolution_time = self._estimate_resolution_time(category, complexity, priority)
        
        # Determine recommended agents
        recommended_agents = self._determine_recommended_agents(category, complexity, requires_escalation)
        
        # Generate routing reason
        routing_reason = self._generate_routing_reason(category, priority, complexity, requires_escalation)
        
        return TicketMetadata(
            category=category,
            priority=priority,
            complexity=complexity,
            urgency_score=urgency_score,
            requires_escalation=requires_escalation,
            estimated_resolution_time=resolution_time,
            recommended_agents=recommended_agents,
            routing_reason=routing_reason
        )
    
    def _determine_category(self, content: str) -> TicketCategory:
        """Determine ticket category based on content"""
        category_scores = {}
        
        for category, keywords in self.classification_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content)
            category_scores[category] = score
        
        # Find category with highest score
        if category_scores["escalation"] > 0:
            return TicketCategory.ESCALATION
        
        max_score = max(category_scores.values())
        if max_score == 0:
            return TicketCategory.GENERAL
        
        for category, score in category_scores.items():
            if score == max_score:
                return TicketCategory(category)
        
        return TicketCategory.GENERAL
    
    def _determine_priority(self, content: str, metadata: Dict[str, Any] = None) -> TicketPriority:
        """Determine ticket priority based on content and metadata"""
        priority_scores = {priority.value: 0 for priority in TicketPriority}
        
        # Score based on content keywords
        for priority, keywords in self.priority_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content)
            priority_scores[priority] = score
        
        # Adjust based on metadata
        if metadata:
            # Check if user is premium/vip
            if metadata.get("user_type") == "premium":
                priority_scores["high"] += 1
            
            # Check if ticket is from blocked user
            if metadata.get("user_blocked", False):
                priority_scores["urgent"] += 1
            
            # Check ticket age
            created_at = metadata.get("created_at")
            if created_at:
                age_hours = (datetime.now() - created_at).total_seconds() / 3600
                if age_hours > 24:
                    priority_scores["high"] += 1
                if age_hours > 48:
                    priority_scores["urgent"] += 1
        
        # Find highest priority
        max_score = max(priority_scores.values())
        
        # If no keywords matched, default to medium
        if max_score == 0:
            return TicketPriority.MEDIUM
        
        for priority, score in priority_scores.items():
            if score == max_score:
                return TicketPriority(priority)
        
        return TicketPriority.MEDIUM
    
    def _determine_complexity(self, content: str) -> TicketComplexity:
        """Determine ticket complexity based on content"""
        complexity_scores = {complexity.value: 0 for complexity in TicketComplexity}
        
        for complexity, indicators in self.complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content)
            complexity_scores[complexity] = score
        
        # Additional complexity factors
        word_count = len(content.split())
        if word_count > 100:
            complexity_scores["complex"] += 1
        elif word_count > 50:
            complexity_scores["moderate"] += 1
        else:
            complexity_scores["simple"] += 1
        
        # Check for multiple issues
        if content.count("and") > 2 or content.count(",") > 5:
            complexity_scores["complex"] += 1
        
        max_score = max(complexity_scores.values())
        for complexity, score in complexity_scores.items():
            if score == max_score:
                return TicketComplexity(complexity)
        
        return TicketComplexity.MODERATE
    
    def _calculate_urgency_score(self, content: str, priority: TicketPriority, metadata: Dict[str, Any] = None) -> float:
        """Calculate urgency score (0.0 to 1.0)"""
        score = 0.0
        
        # Base score from priority
        priority_scores = {
            TicketPriority.LOW: 0.1,
            TicketPriority.MEDIUM: 0.3,
            TicketPriority.HIGH: 0.6,
            TicketPriority.URGENT: 0.9
        }
        score += priority_scores[priority]
        
        # Content-based urgency indicators
        urgency_words = ["urgent", "emergency", "critical", "immediately", "asap", "now", "broken", "not working"]
        urgency_count = sum(1 for word in urgency_words if word in content)
        score += min(urgency_count * 0.1, 0.3)
        
        # Metadata-based adjustments
        if metadata:
            if metadata.get("user_type") == "premium":
                score += 0.1
            if metadata.get("user_blocked", False):
                score += 0.2
            if metadata.get("previous_tickets", 0) > 5:
                score += 0.1
        
        return min(score, 1.0)
    
    def _check_escalation_required(self, content: str, priority: TicketPriority, urgency_score: float) -> bool:
        """Check if ticket requires escalation to human agent"""
        content_lower = content.lower()
        
        # High urgency or priority
        if priority == TicketPriority.URGENT or urgency_score > 0.8:
            return True
        
        # Escalation keywords
        escalation_words = ["human", "agent", "representative", "supervisor", "manager"]
        if any(word in content_lower for word in escalation_words):
            return True
        
        # Legal or security issues
        legal_words = ["legal", "fraud", "unauthorized", "hacked", "compromised", "dispute", "complaint"]
        if any(word in content_lower for word in legal_words):
            return True
        
        # Emergency keywords
        emergency_words = ["urgent", "emergency", "critical", "immediately", "asap"]
        if any(word in content_lower for word in emergency_words):
            return True
        
        return False
    
    def _estimate_resolution_time(self, category: TicketCategory, complexity: TicketComplexity, priority: TicketPriority) -> str:
        """Estimate resolution time based on ticket characteristics"""
        base_times = {
            TicketCategory.TECHNICAL: {"simple": "2-4 hours", "moderate": "4-8 hours", "complex": "8-24 hours"},
            TicketCategory.BILLING: {"simple": "1-2 hours", "moderate": "2-4 hours", "complex": "4-8 hours"},
            TicketCategory.ACCOUNT: {"simple": "1-2 hours", "moderate": "2-4 hours", "complex": "4-8 hours"},
            TicketCategory.GENERAL: {"simple": "1-2 hours", "moderate": "2-4 hours", "complex": "4-8 hours"},
            TicketCategory.ESCALATION: {"simple": "2-4 hours", "moderate": "4-8 hours", "complex": "8-24 hours"}
        }
        
        complexity_key = complexity.value
        base_time = base_times[category][complexity_key]
        
        # Adjust for priority
        if priority == TicketPriority.URGENT:
            return "1-2 hours"
        elif priority == TicketPriority.HIGH:
            return base_time.split("-")[0] + "-" + str(int(base_time.split("-")[1].split()[0]) // 2) + " hours"
        
        return base_time
    
    def _determine_recommended_agents(self, category: TicketCategory, complexity: TicketComplexity, requires_escalation: bool) -> List[str]:
        """Determine recommended agents for the ticket"""
        if requires_escalation:
            return ["ESCALATION"]
        
        # Base agent mapping
        category_agents = {
            TicketCategory.TECHNICAL: ["TECHNICAL"],
            TicketCategory.BILLING: ["BILLING"],
            TicketCategory.ACCOUNT: ["ACCOUNT"],
            TicketCategory.GENERAL: ["KNOWLEDGE_BASE"],
            TicketCategory.ESCALATION: ["ESCALATION"]
        }
        
        base_agents = category_agents[category]
        
        # Add additional agents for complex tickets
        if complexity == TicketComplexity.COMPLEX:
            if category == TicketCategory.TECHNICAL:
                base_agents.extend(["KNOWLEDGE_BASE", "RAG"])
            elif category == TicketCategory.BILLING:
                base_agents.extend(["ACCOUNT", "KNOWLEDGE_BASE"])
            elif category == TicketCategory.ACCOUNT:
                base_agents.extend(["KNOWLEDGE_BASE", "RAG"])
            else:
                base_agents.extend(["RAG", "KNOWLEDGE_BASE"])
        
        return list(set(base_agents))  # Remove duplicates
    
    def _generate_routing_reason(self, category: TicketCategory, priority: TicketPriority, complexity: TicketComplexity, requires_escalation: bool) -> str:
        """Generate human-readable routing reason"""
        if requires_escalation:
            return f"Escalation required due to {priority.value} priority and complex nature"
        
        reasons = []
        reasons.append(f"Classified as {category.value} category")
        reasons.append(f"Priority level: {priority.value}")
        reasons.append(f"Complexity: {complexity.value}")
        
        if complexity == TicketComplexity.COMPLEX:
            reasons.append("Multiple agents recommended for comprehensive resolution")
        
        return "; ".join(reasons)
    
    def route_ticket(self, ticket_content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route a ticket to appropriate agents
        
        Args:
            ticket_content: The ticket description/content
            metadata: Additional ticket metadata
            
        Returns:
            Dictionary with routing decision and metadata
        """
        # Classify the ticket
        ticket_metadata = self.classify_ticket(ticket_content, metadata)
        
        # Create routing decision
        routing_decision = {
            "ticket_id": metadata.get("ticket_id", "unknown"),
            "category": ticket_metadata.category.value,
            "priority": ticket_metadata.priority.value,
            "complexity": ticket_metadata.complexity.value,
            "urgency_score": ticket_metadata.urgency_score,
            "requires_escalation": ticket_metadata.requires_escalation,
            "estimated_resolution_time": ticket_metadata.estimated_resolution_time,
            "recommended_agents": ticket_metadata.recommended_agents,
            "routing_reason": ticket_metadata.routing_reason,
            "routing_timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        return routing_decision
    
    def get_routing_statistics(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get routing statistics from a list of tickets"""
        stats = {
            "total_tickets": len(tickets),
            "category_distribution": {},
            "priority_distribution": {},
            "complexity_distribution": {},
            "escalation_rate": 0,
            "average_urgency_score": 0.0,
            "agent_workload": {}
        }
        
        total_urgency = 0.0
        escalation_count = 0
        
        for ticket in tickets:
            # Category distribution
            category = ticket.get("category", "unknown")
            stats["category_distribution"][category] = stats["category_distribution"].get(category, 0) + 1
            
            # Priority distribution
            priority = ticket.get("priority", "unknown")
            stats["priority_distribution"][priority] = stats["priority_distribution"].get(priority, 0) + 1
            
            # Complexity distribution
            complexity = ticket.get("complexity", "unknown")
            stats["complexity_distribution"][complexity] = stats["complexity_distribution"].get(complexity, 0) + 1
            
            # Escalation rate
            if ticket.get("requires_escalation", False):
                escalation_count += 1
            
            # Average urgency score
            total_urgency += ticket.get("urgency_score", 0.0)
            
            # Agent workload
            for agent in ticket.get("recommended_agents", []):
                stats["agent_workload"][agent] = stats["agent_workload"].get(agent, 0) + 1
        
        if tickets:
            stats["escalation_rate"] = escalation_count / len(tickets)
            stats["average_urgency_score"] = total_urgency / len(tickets)
        
        return stats
