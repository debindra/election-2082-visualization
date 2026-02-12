"""
Pydantic models for RAG chatbot API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str = Field(..., description="User's natural language query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")
    top_k: int = Field(5, ge=1, le=20, description="Number of retrieval results")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="Generated answer from LLM")
    sources: List[Dict[str, Any]] = Field(..., description="Retrieved source documents")
    sql_used: Optional[str] = Field(None, description="SQL query executed if applicable")
    analytics_used: Optional[Dict[str, Any]] = Field(None, description="Analytics data if used")
    query_type: str = Field(..., description="Type of query processed")
    intent: Optional[str] = Field(None, description="Intent of the query (polling, candidate, etc.)")
    entities: Optional[Dict[str, Any]] = Field(None, description="Extracted entities from the query")
    method: str = Field(..., description="Method used to process query")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AnalyticsRequest(BaseModel):
    """Request model for analytics endpoint"""
    query_type: str = Field(..., description="Type of analytics query")
    params: Dict[str, Any] = Field(..., description="Parameters for analytics query")


class AnalyticsResponse(BaseModel):
    """Response model for analytics endpoint"""
    query_type: str = Field(..., description="Type of analytics query")
    result: Dict[str, Any] = Field(..., description="Analytics results")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Query metadata")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="System status")
    embedding_model: str = Field(..., description="Embedding model being used")
    vector_index_loaded: bool = Field(..., description="Whether vector index is loaded")
    analytics_loaded: bool = Field(..., description="Whether analytics data is loaded")
    deepseek_configured: bool = Field(..., description="Whether DeepSeek API is configured")


class ErrorDetail(BaseModel):
    """Error detail model"""
    detail: str = Field(..., description="Error message")
