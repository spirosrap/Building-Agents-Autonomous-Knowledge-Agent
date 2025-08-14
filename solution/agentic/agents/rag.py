"""
RAG Agent - Retrieval-Augmented Generation Specialist

This agent is responsible for:
- Performing semantic search across knowledge base
- Generating contextual responses
- Providing real-time information retrieval
- Maintaining search relevance and accuracy
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import re

class RAGAgent:
    def __init__(self, llm: ChatOpenAI, knowledge_base_data: List[Dict[str, Any]]):
        self.llm = llm
        self.knowledge_base = knowledge_base_data
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the RAG agent"""
        return """You are the RAG (Retrieval-Augmented Generation) Agent for Uda-hub, a customer support system for CultPass users. Your role is to:

1. PERFORM semantic search across the knowledge base
2. GENERATE contextual responses using retrieved information
3. PROVIDE real-time information retrieval
4. MAINTAIN search relevance and accuracy

You excel at:
- Complex queries requiring multiple information sources
- Contextual understanding and synthesis
- Providing comprehensive, well-structured responses
- Maintaining accuracy while being helpful

Always base your responses on the retrieved knowledge base information. If information is not available, acknowledge this and suggest contacting support."""
    
    def semantic_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search across knowledge base"""
        query_lower = query.lower()
        relevant_articles = []
        
        # Enhanced semantic search with multiple relevance factors
        for article in self.knowledge_base:
            relevance_score = self._calculate_semantic_relevance(article, query_lower)
            if relevance_score > 0.2:  # Lower threshold for broader search
                article_copy = article.copy()
                article_copy["relevance_score"] = relevance_score
                relevant_articles.append(article_copy)
        
        # Sort by relevance and return top results
        relevant_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_articles[:max_results]
    
    def _calculate_semantic_relevance(self, article: Dict[str, Any], query: str) -> float:
        """Calculate semantic relevance using multiple factors"""
        title = article.get("title", "").lower()
        content = article.get("content", "").lower()
        tags = article.get("tags", "").lower()
        
        # Split query into words
        query_words = set(query.split())
        
        # Title relevance (highest weight)
        title_words = set(title.split())
        title_matches = len(query_words.intersection(title_words))
        title_score = title_matches / len(query_words) if query_words else 0
        
        # Content relevance (medium weight)
        content_words = set(content.split())
        content_matches = len(query_words.intersection(content_words))
        content_score = content_matches / len(query_words) if query_words else 0
        
        # Tags relevance (high weight)
        tag_words = set(tags.split(", "))
        tag_matches = len(query_words.intersection(tag_words))
        tag_score = tag_matches / len(query_words) if query_words else 0
        
        # Semantic similarity (additional weight for related concepts)
        semantic_score = self._calculate_semantic_similarity(query, content)
        
        # Weighted combination
        relevance_score = (
            title_score * 0.4 + 
            content_score * 0.3 + 
            tag_score * 0.2 + 
            semantic_score * 0.1
        )
        
        return relevance_score
    
    def _calculate_semantic_similarity(self, query: str, content: str) -> float:
        """Calculate semantic similarity between query and content"""
        # Simple keyword-based semantic similarity
        # In a real implementation, this would use embeddings
        
        # Define semantic groups
        semantic_groups = {
            "login": ["login", "password", "access", "authentication", "sign in"],
            "events": ["event", "reservation", "booking", "experience", "activity"],
            "billing": ["payment", "subscription", "billing", "cost", "refund"],
            "account": ["profile", "preferences", "settings", "account", "user"],
            "technical": ["error", "problem", "issue", "bug", "technical"]
        }
        
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Find matching semantic groups
        query_groups = []
        content_groups = []
        
        for group_name, keywords in semantic_groups.items():
            if any(keyword in query_lower for keyword in keywords):
                query_groups.append(group_name)
            if any(keyword in content_lower for keyword in keywords):
                content_groups.append(group_name)
        
        # Calculate overlap
        if query_groups and content_groups:
            overlap = len(set(query_groups).intersection(set(content_groups)))
            return overlap / max(len(query_groups), len(content_groups))
        
        return 0.0
    
    def generate_contextual_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate contextual response using RAG"""
        if not context:
            return "I don't have specific information about that in our knowledge base. Please contact our customer support team for assistance."
        
        # Create context from retrieved articles
        context_text = self._create_context_from_articles(context)
        
        # Generate response using LLM
        response_prompt = f"""Based on the following knowledge base information, provide a comprehensive and helpful response to the user query: "{query}"

Retrieved Information:
{context_text}

Provide a well-structured, accurate, and helpful response that directly addresses the user's query. If the information doesn't fully answer their question, acknowledge this and suggest contacting support for additional help."""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=response_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _create_context_from_articles(self, articles: List[Dict[str, Any]]) -> str:
        """Create context string from retrieved articles"""
        context = ""
        for i, article in enumerate(articles, 1):
            context += f"\n{i}. Title: {article.get('title', 'No title')}\n"
            context += f"   Content: {article.get('content', 'No content')}\n"
            context += f"   Tags: {article.get('tags', 'No tags')}\n"
            context += f"   Relevance: {article.get('relevance_score', 0):.2f}\n"
        return context
    
    def update_knowledge_base(self, new_content: str) -> bool:
        """Update knowledge base with new content (placeholder)"""
        # In a real implementation, this would update the vector database
        return True
    
    def rank_search_results(self, articles: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank search results by relevance"""
        for article in articles:
            if "relevance_score" not in article:
                article["relevance_score"] = self._calculate_semantic_relevance(article, query.lower())
        
        articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        return articles
    
    def get_related_articles(self, query: str, max_related: int = 3) -> List[Dict[str, Any]]:
        """Get related articles for additional context"""
        # Perform broader search for related articles
        related_articles = self.semantic_search(query, max_related * 2)
        
        # Filter for articles that are related but not too similar
        filtered_articles = []
        seen_concepts = set()
        
        for article in related_articles:
            article_tags = set(article.get("tags", "").lower().split(", "))
            if not article_tags.intersection(seen_concepts):
                filtered_articles.append(article)
                seen_concepts.update(article_tags)
            
            if len(filtered_articles) >= max_related:
                break
        
        return filtered_articles
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query using RAG approach"""
        # Perform semantic search
        search_results = self.semantic_search(query)
        
        # Get related articles for additional context
        related_articles = self.get_related_articles(query)
        
        # Generate contextual response
        response = self.generate_contextual_response(query, search_results)
        
        # Prepare metadata
        metadata = {
            "agent": "RAG",
            "search_results_count": len(search_results),
            "related_articles_count": len(related_articles),
            "top_relevance_score": search_results[0]["relevance_score"] if search_results else 0,
            "search_query": query
        }
        
        return {
            "agent": "RAG",
            "response": response,
            "search_results": search_results,
            "related_articles": related_articles,
            "metadata": metadata,
            "confidence": min(1.0, len(search_results) * 0.2)  # Higher confidence with more results
        }
    
    def enhance_response_with_context(self, base_response: str, query: str, additional_context: List[Dict[str, Any]]) -> str:
        """Enhance a base response with additional context"""
        if not additional_context:
            return base_response
        
        enhancement_prompt = f"""Enhance this response with additional context:

Original Response: {base_response}

User Query: {query}

Additional Context:
{self._create_context_from_articles(additional_context)}

Provide an enhanced response that incorporates the additional context while maintaining the original response's accuracy and helpfulness."""
        
        messages = [
            SystemMessage(content="You are a response enhancement expert. Improve responses by incorporating additional context."),
            HumanMessage(content=enhancement_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
