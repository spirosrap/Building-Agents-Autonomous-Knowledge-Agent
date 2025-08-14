"""
Knowledge Base Agent - Expert in Retrieving and Presenting Support Information

This agent is responsible for:
- Searching and retrieving relevant knowledge base articles
- Providing accurate support information
- Suggesting relevant articles based on user queries
- Updating knowledge base with new information
- Maintaining article relevance and accuracy
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import re

class KnowledgeBaseAgent:
    def __init__(self, llm: ChatOpenAI, knowledge_base_data: List[Dict[str, Any]]):
        self.llm = llm
        self.knowledge_base = knowledge_base_data
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the knowledge base agent"""
        return """You are the Knowledge Base Agent for Uda-hub, a customer support system for CultPass users. Your role is to:

1. SEARCH and retrieve relevant knowledge base articles
2. PROVIDE accurate support information based on the knowledge base
3. SUGGEST relevant articles based on user queries
4. MAINTAIN article relevance and accuracy

You have access to a comprehensive knowledge base with articles covering:
- How to reserve events and use the app
- Subscription benefits and pricing
- Account management and preferences
- Technical troubleshooting
- Billing and payment information
- Premium events and features
- Customer support contact information

Always base your responses on the available knowledge base articles. If you don't find relevant information, suggest contacting customer support."""
    
    def search_knowledge_base(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant articles"""
        query_lower = query.lower()
        relevant_articles = []
        
        for article in self.knowledge_base:
            relevance_score = self._calculate_relevance(article, query_lower)
            if relevance_score > 0.3:  # Threshold for relevance
                article_copy = article.copy()
                article_copy["relevance_score"] = relevance_score
                relevant_articles.append(article_copy)
        
        # Sort by relevance score and return top results
        relevant_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_articles[:max_results]
    
    def _calculate_relevance(self, article: Dict[str, Any], query: str) -> float:
        """Calculate relevance score between article and query"""
        title = article.get("title", "").lower()
        content = article.get("content", "").lower()
        tags = article.get("tags", "").lower()
        
        # Split query into words
        query_words = set(query.split())
        
        # Calculate title relevance (highest weight)
        title_words = set(title.split())
        title_matches = len(query_words.intersection(title_words))
        title_score = title_matches / len(query_words) if query_words else 0
        
        # Calculate content relevance
        content_words = set(content.split())
        content_matches = len(query_words.intersection(content_words))
        content_score = content_matches / len(query_words) if query_words else 0
        
        # Calculate tags relevance
        tag_words = set(tags.split(", "))
        tag_matches = len(query_words.intersection(tag_words))
        tag_score = tag_matches / len(query_words) if query_words else 0
        
        # Weighted combination
        relevance_score = (title_score * 0.5) + (content_score * 0.3) + (tag_score * 0.2)
        
        return relevance_score
    
    def rank_articles(self, articles: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank articles by relevance to query"""
        for article in articles:
            if "relevance_score" not in article:
                article["relevance_score"] = self._calculate_relevance(article, query.lower())
        
        articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        return articles
    
    def generate_response(self, articles: List[Dict[str, Any]], query: str) -> str:
        """Generate response based on knowledge base articles"""
        if not articles:
            return "I don't have specific information about that in our knowledge base. Please contact our customer support team for assistance."
        
        # Create context from articles
        context = self._create_context_from_articles(articles)
        
        response_prompt = f"""Based on the following knowledge base articles, provide a helpful response to the user query: "{query}"

Knowledge Base Articles:
{context}

Provide a clear, accurate, and helpful response. If the articles don't fully address the query, acknowledge this and suggest contacting support for additional help."""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=response_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _create_context_from_articles(self, articles: List[Dict[str, Any]]) -> str:
        """Create context string from articles"""
        context = ""
        for i, article in enumerate(articles, 1):
            context += f"\n{i}. Title: {article.get('title', 'No title')}\n"
            context += f"   Content: {article.get('content', 'No content')}\n"
            context += f"   Tags: {article.get('tags', 'No tags')}\n"
            context += f"   Relevance: {article.get('relevance_score', 0):.2f}\n"
        return context
    
    def suggest_articles(self, query: str, max_suggestions: int = 3) -> List[Dict[str, Any]]:
        """Suggest relevant articles based on query"""
        relevant_articles = self.search_knowledge_base(query, max_suggestions)
        return relevant_articles
    
    def get_article_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Get specific article by title"""
        for article in self.knowledge_base:
            if article.get("title", "").lower() == title.lower():
                return article
        return None
    
    def get_articles_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get articles by tag"""
        tag_lower = tag.lower()
        matching_articles = []
        
        for article in self.knowledge_base:
            article_tags = article.get("tags", "").lower()
            if tag_lower in article_tags:
                matching_articles.append(article)
        
        return matching_articles
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user query and return response with metadata"""
        try:
            # Check if knowledge result is available in context
            knowledge_result = context.get("knowledge_result") if context else None
            
            if knowledge_result:
                # Use the pre-computed knowledge retrieval result
                return {
                    "agent": "KNOWLEDGE_BASE",
                    "response": knowledge_result.response,
                    "confidence": knowledge_result.confidence_level.value,
                    "articles_used": [{"title": a.title, "relevance": a.relevance_score} for a in knowledge_result.articles],
                    "should_escalate": knowledge_result.should_escalate,
                    "escalation_reason": knowledge_result.escalation_reason,
                    "retrieval_metadata": knowledge_result.retrieval_metadata
                }
            else:
                # Fallback to original search method
                relevant_articles = self.search_knowledge_base(query)
                response = self.generate_response(relevant_articles, query)
                
                # Prepare metadata
                metadata = {
                    "agent": "KNOWLEDGE_BASE",
                    "articles_found": len(relevant_articles),
                    "top_article": relevant_articles[0] if relevant_articles else None,
                    "all_articles": relevant_articles,
                    "confidence": min(1.0, len(relevant_articles) * 0.3)
                }
                
                return {
                    "agent": "KNOWLEDGE_BASE",
                    "response": response,
                    "metadata": metadata,
                    "articles_used": relevant_articles
                }
        except Exception as e:
            return {
                "agent": "KNOWLEDGE_BASE",
                "response": f"I encountered an error while searching the knowledge base: {str(e)}",
                "confidence": "low",
                "articles_used": []
            }
