"""
Search Tools for Multi-Agent System

Tools for searching and retrieving information from:
- Knowledge base
- User data
- Experience data
"""

from langchain.tools import BaseTool
from typing import Dict, List, Any, Optional
import json

class SearchTool(BaseTool):
    name: str = "search_tool"
    description: str = "Tool for searching knowledge base and other data sources"
    knowledge_base: List[Dict[str, Any]] = []
    
    def __init__(self, knowledge_base_data: List[Dict[str, Any]]):
        super().__init__()
        self.knowledge_base = knowledge_base_data
    
    def _run(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search knowledge base and return relevant results"""
        try:
            search_type = kwargs.get("type", "semantic")
            max_results = kwargs.get("max_results", 5)
            
            if search_type == "semantic":
                return self._semantic_search(query, max_results)
            elif search_type == "keyword":
                return self._keyword_search(query, max_results)
            elif search_type == "tag":
                return self._tag_search(query, max_results)
            else:
                return {"error": f"Unknown search type: {search_type}"}
        except Exception as e:
            return {"error": f"Search operation failed: {str(e)}"}
    
    def _semantic_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Perform semantic search across knowledge base"""
        query_lower = query.lower()
        relevant_articles = []
        
        for article in self.knowledge_base:
            relevance_score = self._calculate_semantic_relevance(article, query_lower)
            if relevance_score > 0.2:  # Threshold for relevance
                article_copy = article.copy()
                article_copy["relevance_score"] = relevance_score
                relevant_articles.append(article_copy)
        
        # Sort by relevance and return top results
        relevant_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = relevant_articles[:max_results]
        
        return {
            "query": query,
            "search_type": "semantic",
            "results": results,
            "total_found": len(relevant_articles),
            "returned": len(results)
        }
    
    def _keyword_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Perform keyword-based search"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        relevant_articles = []
        
        for article in self.knowledge_base:
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            tags = article.get("tags", "").lower()
            
            # Count keyword matches
            title_matches = sum(1 for word in query_words if word in title)
            content_matches = sum(1 for word in query_words if word in content)
            tag_matches = sum(1 for word in query_words if word in tags)
            
            # Calculate relevance score
            relevance_score = (title_matches * 3 + content_matches * 2 + tag_matches * 2) / len(query_words)
            
            if relevance_score > 0.1:  # Lower threshold for keyword search
                article_copy = article.copy()
                article_copy["relevance_score"] = relevance_score
                relevant_articles.append(article_copy)
        
        # Sort by relevance and return top results
        relevant_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = relevant_articles[:max_results]
        
        return {
            "query": query,
            "search_type": "keyword",
            "results": results,
            "total_found": len(relevant_articles),
            "returned": len(results)
        }
    
    def _tag_search(self, tag: str, max_results: int) -> Dict[str, Any]:
        """Search articles by tag"""
        tag_lower = tag.lower()
        relevant_articles = []
        
        for article in self.knowledge_base:
            article_tags = article.get("tags", "").lower()
            if tag_lower in article_tags:
                article_copy = article.copy()
                article_copy["relevance_score"] = 1.0  # Exact tag match
                relevant_articles.append(article_copy)
        
        results = relevant_articles[:max_results]
        
        return {
            "query": tag,
            "search_type": "tag",
            "results": results,
            "total_found": len(relevant_articles),
            "returned": len(results)
        }
    
    def _calculate_semantic_relevance(self, article: Dict[str, Any], query: str) -> float:
        """Calculate semantic relevance between article and query"""
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
        
        # Weighted combination
        relevance_score = (title_score * 0.5) + (content_score * 0.3) + (tag_score * 0.2)
        
        return relevance_score
    
    def search_by_category(self, category: str) -> Dict[str, Any]:
        """Search articles by category/topic"""
        category_lower = category.lower()
        relevant_articles = []
        
        # Define category mappings
        category_keywords = {
            "technical": ["login", "password", "error", "bug", "technical", "troubleshooting"],
            "billing": ["payment", "subscription", "billing", "refund", "cost", "premium"],
            "account": ["account", "profile", "preferences", "settings", "transfer"],
            "events": ["event", "reservation", "booking", "experience", "qr code"],
            "general": ["how to", "what is", "guide", "help", "information"]
        }
        
        keywords = category_keywords.get(category_lower, [category_lower])
        
        for article in self.knowledge_base:
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            tags = article.get("tags", "").lower()
            
            # Check if any category keyword matches
            for keyword in keywords:
                if (keyword in title or keyword in content or keyword in tags):
                    article_copy = article.copy()
                    article_copy["relevance_score"] = 0.8
                    relevant_articles.append(article_copy)
                    break
        
        return {
            "category": category,
            "results": relevant_articles,
            "total_found": len(relevant_articles)
        }
    
    def get_popular_articles(self, limit: int = 5) -> Dict[str, Any]:
        """Get popular/frequently accessed articles"""
        # In a real implementation, this would track article access
        # For now, return articles with common topics
        popular_topics = ["reservation", "subscription", "login", "payment", "account"]
        popular_articles = []
        
        for topic in popular_topics:
            topic_articles = self._tag_search(topic, 1)
            if topic_articles["results"]:
                popular_articles.extend(topic_articles["results"])
        
        return {
            "type": "popular",
            "results": popular_articles[:limit],
            "total_found": len(popular_articles)
        }
    
    def suggest_related_articles(self, article_id: str, limit: int = 3) -> Dict[str, Any]:
        """Suggest related articles based on a given article"""
        # Find the target article
        target_article = None
        for article in self.knowledge_base:
            if article.get("article_id") == article_id:
                target_article = article
                break
        
        if not target_article:
            return {"error": "Article not found"}
        
        # Get tags from target article
        target_tags = set(target_article.get("tags", "").lower().split(", "))
        
        # Find articles with similar tags
        related_articles = []
        for article in self.knowledge_base:
            if article.get("article_id") != article_id:  # Exclude the target article
                article_tags = set(article.get("tags", "").lower().split(", "))
                overlap = len(target_tags.intersection(article_tags))
                
                if overlap > 0:
                    article_copy = article.copy()
                    article_copy["relevance_score"] = overlap / len(target_tags)
                    related_articles.append(article_copy)
        
        # Sort by relevance and return top results
        related_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = related_articles[:limit]
        
        return {
            "target_article": target_article.get("title"),
            "results": results,
            "total_found": len(related_articles),
            "returned": len(results)
        }
