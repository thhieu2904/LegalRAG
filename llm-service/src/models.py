"""
Pydantic models for LLM Service API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateRequest(BaseModel):
    """Request model for text generation."""
    
    prompt: str = Field(
        ...,
        description="Input prompt for text generation",
        min_length=1,
        examples=["Điều kiện thành lập công ty TNHH là gì?"]
    )
    
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens to generate (default: from env)",
        ge=1,
        le=4096,
        examples=[512]
    )
    
    temperature: Optional[float] = Field(
        default=None,
        description="Sampling temperature (0.0-2.0)",
        ge=0.0,
        le=2.0,
        examples=[0.7]
    )
    
    top_p: Optional[float] = Field(
        default=None,
        description="Nucleus sampling threshold",
        ge=0.0,
        le=1.0,
        examples=[0.9]
    )
    
    top_k: Optional[int] = Field(
        default=None,
        description="Top-K sampling",
        ge=0,
        le=100,
        examples=[40]
    )
    
    repeat_penalty: Optional[float] = Field(
        default=None,
        description="Penalty for repeating tokens",
        ge=1.0,
        le=2.0,
        examples=[1.1]
    )
    
    stop: Optional[List[str]] = Field(
        default=None,
        description="Stop sequences",
        examples=[["###", "USER:"]]
    )


class GenerateResponse(BaseModel):
    """Response model for text generation."""
    
    success: bool = Field(
        ...,
        description="Whether generation was successful"
    )
    
    text: str = Field(
        ...,
        description="Generated text"
    )
    
    prompt_tokens: int = Field(
        ...,
        description="Number of tokens in the prompt"
    )
    
    completion_tokens: int = Field(
        ...,
        description="Number of tokens generated"
    )
    
    total_tokens: int = Field(
        ...,
        description="Total tokens (prompt + completion)"
    )
    
    model: str = Field(
        ...,
        description="Model used for generation"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(
        default="healthy",
        examples=["healthy"]
    )
    
    service: str = Field(
        default="llm-service",
        examples=["llm-service"]
    )
    
    model_loaded: bool = Field(
        ...,
        description="Whether the LLM model is loaded"
    )
    
    model_name: str = Field(
        ...,
        description="Name of the loaded model"
    )
    
    device: str = Field(
        ...,
        description="Device being used (cuda/cpu)"
    )
    
    n_ctx: int = Field(
        ...,
        description="Context window size"
    )
    
    gpu_swap_mode: Optional[bool] = Field(
        default=None,
        description="Whether GPU swap mode is enabled"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(
        ...,
        description="Error message"
    )
    
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )
