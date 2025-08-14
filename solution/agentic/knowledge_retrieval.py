"""
Knowledge Retrieval and Tool Usage System

This module implements a knowledge-based response system with escalation logic
that retrieves relevant knowledge base articles and escalates when no relevant
knowledge is found.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
import json
from dataclasses import dataclass
from enum import Enum
import math
from datetime import datetime

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

@dataclass
class KnowledgeArticle:
    """Knowledge base article with metadata"""
    article_id: str
    title: str
    content: str
    tags: str
    relevance_score: float = 0.0
    confidence_score: float = 0.0

@dataclass
class RetrievalResult:
    """Result of knowledge retrieval operation"""
    articles: List[KnowledgeArticle]
    confidence_level: ConfidenceLevel
    should_escalate: bool
    escalation_reason: str
    response: str
    retrieval_metadata: Dict[str, Any]

class KnowledgeRetrievalSystem:
    """
    Knowledge retrieval system that provides responses based on articles
    and escalates when no relevant knowledge is found.
    """
    
    def __init__(self, knowledge_base_data: List[Dict[str, Any]]):
        self.knowledge_base = self._load_knowledge_base(knowledge_base_data)
        self.confidence_thresholds = {
            ConfidenceLevel.HIGH: 0.7,
            ConfidenceLevel.MEDIUM: 0.5,
            ConfidenceLevel.LOW: 0.3,
            ConfidenceLevel.NONE: 0.0
        }
        self.escalation_threshold = 0.2  # Below this confidence, escalate
    
    def _load_knowledge_base(self, knowledge_base_data: List[Dict[str, Any]]) -> List[KnowledgeArticle]:
        """Load knowledge base articles from data"""
        articles = []
        for article_data in knowledge_base_data:
            article = KnowledgeArticle(
                article_id=article_data.get("article_id", ""),
                title=article_data.get("title", ""),
                content=article_data.get("content", ""),
                tags=article_data.get("tags", "")
            )
            articles.append(article)
        return articles
    
    def retrieve_knowledge(self, query: str, ticket_metadata: Dict[str, Any] = None) -> RetrievalResult:
        """
        Retrieve relevant knowledge base articles based on ticket content
        
        Args:
            query: The ticket content/query
            ticket_metadata: Additional ticket metadata
            
        Returns:
            RetrievalResult with articles, confidence, and escalation decision
        """
        # Calculate relevance scores for all articles
        scored_articles = []
        for article in self.knowledge_base:
            relevance_score = self._calculate_relevance_score(query, article)
            confidence_score = self._calculate_confidence_score(query, article, relevance_score)
            
            scored_article = KnowledgeArticle(
                article_id=article.article_id,
                title=article.title,
                content=article.content,
                tags=article.tags,
                relevance_score=relevance_score,
                confidence_score=confidence_score
            )
            scored_articles.append(scored_article)
        
        # Sort by relevance score (descending)
        scored_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Get top relevant articles
        top_articles = scored_articles[:3]  # Top 3 most relevant
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(top_articles)
        
        # Check if escalation is needed
        should_escalate, escalation_reason = self._check_escalation_needed(
            top_articles, confidence_level, query, ticket_metadata
        )
        
        # Generate response
        response = self._generate_response(top_articles, confidence_level, should_escalate)
        
        # Create retrieval metadata
        retrieval_metadata = {
            "total_articles_searched": len(self.knowledge_base),
            "articles_retrieved": len(top_articles),
            "highest_relevance_score": top_articles[0].relevance_score if top_articles else 0.0,
            "average_confidence": sum(a.confidence_score for a in top_articles) / len(top_articles) if top_articles else 0.0,
            "retrieval_timestamp": datetime.now().isoformat(),
            "query_length": len(query),
            "ticket_metadata": ticket_metadata or {}
        }
        
        return RetrievalResult(
            articles=top_articles,
            confidence_level=confidence_level,
            should_escalate=should_escalate,
            escalation_reason=escalation_reason,
            response=response,
            retrieval_metadata=retrieval_metadata
        )
    
    def _calculate_relevance_score(self, query: str, article: KnowledgeArticle) -> float:
        """Calculate relevance score between query and article"""
        query_lower = query.lower()
        article_content_lower = article.content.lower()
        article_title_lower = article.title.lower()
        article_tags_lower = article.tags.lower()
        
        # Extract keywords from query
        query_keywords = self._extract_keywords(query_lower)
        
        # Calculate content relevance
        content_score = self._calculate_keyword_match(query_keywords, article_content_lower)
        
        # Calculate title relevance (weighted higher)
        title_score = self._calculate_keyword_match(query_keywords, article_title_lower) * 1.5
        
        # Calculate tag relevance
        tag_score = self._calculate_keyword_match(query_keywords, article_tags_lower) * 2.0
        
        # Calculate semantic similarity (simplified)
        semantic_score = self._calculate_semantic_similarity(query_lower, article_content_lower)
        
        # Combine scores with weights
        total_score = (
            content_score * 0.4 +
            title_score * 0.3 +
            tag_score * 0.2 +
            semantic_score * 0.1
        )
        
        return min(total_score, 1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours',
            'his', 'hers', 'ours', 'theirs', 'what', 'when', 'where', 'why', 'how', 'who',
            'which', 'whom', 'whose', 'if', 'then', 'else', 'because', 'since', 'while',
            'before', 'after', 'during', 'until', 'unless', 'although', 'though', 'even',
            'though', 'as', 'so', 'than', 'such', 'very', 'too', 'just', 'only', 'also',
            'even', 'still', 'again', 'once', 'twice', 'first', 'second', 'third', 'last',
            'next', 'previous', 'current', 'new', 'old', 'good', 'bad', 'big', 'small',
            'high', 'low', 'long', 'short', 'fast', 'slow', 'easy', 'hard', 'simple',
            'complex', 'important', 'urgent', 'critical', 'necessary', 'optional'
        }
        
        # Extract words and filter
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_keyword_match(self, query_keywords: List[str], text: str) -> float:
        """Calculate keyword match score"""
        if not query_keywords:
            return 0.0
        
        matches = 0
        for keyword in query_keywords:
            if keyword in text:
                matches += 1
        
        return matches / len(query_keywords)
    
    def _calculate_semantic_similarity(self, query: str, content: str) -> float:
        """Calculate semantic similarity between query and content"""
        # Simplified semantic similarity using word overlap
        query_words = set(re.findall(r'\b\w+\b', query))
        content_words = set(re.findall(r'\b\w+\b', content))
        
        if not query_words or not content_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        
        return len(intersection) / len(union)
    
    def _calculate_confidence_score(self, query: str, article: KnowledgeArticle, relevance_score: float) -> float:
        """Calculate confidence score for article relevance"""
        # Base confidence on relevance score
        confidence = relevance_score
        
        # Adjust based on query-article length ratio
        query_length = len(query.split())
        article_length = len(article.content.split())
        
        if article_length > 0:
            length_ratio = min(query_length / article_length, 2.0)
            confidence *= (0.8 + 0.2 * length_ratio)
        
        # Adjust based on tag relevance
        query_lower = query.lower()
        tag_relevance = sum(1 for tag in article.tags.split(',') if tag.strip().lower() in query_lower)
        if tag_relevance > 0:
            confidence *= 1.1
        
        return min(confidence, 1.0)
    
    def _determine_confidence_level(self, articles: List[KnowledgeArticle]) -> ConfidenceLevel:
        """Determine confidence level based on article scores"""
        if not articles:
            return ConfidenceLevel.NONE
        
        # Use the highest confidence score
        max_confidence = max(article.confidence_score for article in articles)
        
        if max_confidence >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif max_confidence >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        elif max_confidence >= self.confidence_thresholds[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.NONE
    
    def _check_escalation_needed(self, articles: List[KnowledgeArticle], confidence_level: ConfidenceLevel, 
                                query: str, ticket_metadata: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Check if escalation is needed"""
        # Check confidence threshold
        if confidence_level == ConfidenceLevel.NONE:
            return True, "No relevant knowledge base articles found"
        
        # Check if highest confidence is below escalation threshold
        if articles and articles[0].confidence_score < self.escalation_threshold:
            return True, f"Low confidence ({articles[0].confidence_score:.2f}) below threshold ({self.escalation_threshold})"
        
        # Check for escalation keywords in query
        escalation_keywords = [
            'urgent', 'emergency', 'critical', 'immediately', 'human', 'agent',
            'representative', 'supervisor', 'manager', 'complaint', 'dispute',
            'legal', 'fraud', 'unauthorized', 'hacked', 'compromised'
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in escalation_keywords):
            return True, "Escalation keywords detected in query"
        
        # Check metadata for escalation indicators
        if ticket_metadata:
            if ticket_metadata.get("user_blocked", False):
                return True, "User account is blocked"
            if ticket_metadata.get("user_type") == "premium" and confidence_level == ConfidenceLevel.LOW:
                return True, "Premium user with low confidence requires escalation"
        
        return False, "Sufficient knowledge base coverage available"
    
    def _generate_response(self, articles: List[KnowledgeArticle], confidence_level: ConfidenceLevel, 
                          should_escalate: bool) -> str:
        """Generate response based on retrieved articles"""
        if should_escalate:
            return self._generate_escalation_response(articles, confidence_level)
        
        if not articles:
            return "I apologize, but I don't have specific information about this topic. Let me escalate this to a human agent who can provide more detailed assistance."
        
        # Generate response based on confidence level
        if confidence_level == ConfidenceLevel.HIGH:
            return self._generate_high_confidence_response(articles)
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return self._generate_medium_confidence_response(articles)
        else:
            return self._generate_low_confidence_response(articles)
    
    def _generate_high_confidence_response(self, articles: List[KnowledgeArticle]) -> str:
        """Generate response for high confidence articles"""
        primary_article = articles[0]
        
        response = f"Based on our knowledge base, here's the information you need:\n\n"
        response += f"**{primary_article.title}**\n\n"
        
        # Extract key points from content
        content_lines = primary_article.content.split('\n')
        key_points = []
        
        for line in content_lines:
            line = line.strip()
            if line and not line.startswith('**') and len(line) > 20:
                key_points.append(line)
                if len(key_points) >= 3:  # Limit to 3 key points
                    break
        
        for point in key_points:
            response += f"• {point}\n"
        
        if len(articles) > 1:
            response += f"\n*Additional relevant information may be available in our knowledge base.*"
        
        return response
    
    def _generate_medium_confidence_response(self, articles: List[KnowledgeArticle]) -> str:
        """Generate response for medium confidence articles"""
        response = "I found some relevant information that might help:\n\n"
        
        for i, article in enumerate(articles[:2], 1):
            response += f"**{i}. {article.title}**\n"
            
            # Provide a brief summary
            content_preview = article.content[:150] + "..." if len(article.content) > 150 else article.content
            response += f"{content_preview}\n\n"
        
        response += "If this doesn't fully address your question, please let me know and I can escalate to a human agent for more specific assistance."
        
        return response
    
    def _generate_low_confidence_response(self, articles: List[KnowledgeArticle]) -> str:
        """Generate response for low confidence articles"""
        response = "I found some general information that might be related to your question:\n\n"
        
        if articles:
            response += f"**{articles[0].title}**\n"
            response += f"{articles[0].content[:100]}...\n\n"
        
        response += "However, this may not fully address your specific question. "
        response += "Would you like me to escalate this to a human agent who can provide more targeted assistance?"
        
        return response
    
    def _generate_escalation_response(self, articles: List[KnowledgeArticle], confidence_level: ConfidenceLevel) -> str:
        """Generate escalation response"""
        response = "I understand your question, but I don't have sufficient information in our knowledge base to provide a complete answer. "
        
        if articles:
            response += f"I found some potentially related information about '{articles[0].title}', but it may not fully address your specific needs. "
        
        response += "I'm escalating this to our human support team who will be able to provide you with more detailed and accurate assistance. "
        response += "You should receive a response within the next few hours."
        
        return response
    
    def get_retrieval_statistics(self, retrieval_results: List[RetrievalResult]) -> Dict[str, Any]:
        """Get statistics from knowledge retrieval operations"""
        stats = {
            "total_queries": len(retrieval_results),
            "escalation_rate": 0.0,
            "confidence_distribution": {},
            "average_articles_retrieved": 0.0,
            "average_relevance_score": 0.0,
            "average_confidence_score": 0.0,
            "successful_retrievals": 0,
            "failed_retrievals": 0
        }
        
        if not retrieval_results:
            return stats
        
        escalation_count = 0
        total_articles = 0
        total_relevance = 0.0
        total_confidence = 0.0
        successful_count = 0
        
        for result in retrieval_results:
            if result.should_escalate:
                escalation_count += 1
            else:
                successful_count += 1
            
            # Confidence distribution
            confidence = result.confidence_level.value
            stats["confidence_distribution"][confidence] = stats["confidence_distribution"].get(confidence, 0) + 1
            
            # Article statistics
            total_articles += len(result.articles)
            if result.articles:
                total_relevance += max(article.relevance_score for article in result.articles)
                total_confidence += max(article.confidence_score for article in result.articles)
        
        stats["escalation_rate"] = escalation_count / len(retrieval_results)
        stats["average_articles_retrieved"] = total_articles / len(retrieval_results)
        stats["average_relevance_score"] = total_relevance / len(retrieval_results)
        stats["average_confidence_score"] = total_confidence / len(retrieval_results)
        stats["successful_retrievals"] = successful_count
        stats["failed_retrievals"] = escalation_count
        
        return stats
