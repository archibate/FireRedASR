"""Pydantic models for request/response schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    """Single transcription result."""

    text: str = Field(..., description="Recognized text")
    rtf: float = Field(..., description="Real-time factor (processing time / audio duration)")
    duration_seconds: float = Field(..., description="Audio duration in seconds")


class BatchTranscriptionResult(BaseModel):
    """Batch transcription response."""

    results: List[TranscriptionResult] = Field(..., description="List of transcription results")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status: 'healthy' or 'unhealthy'")
    model_loaded: bool = Field(..., description="Whether the ASR model is loaded")
    gpu_available: bool = Field(..., description="Whether GPU is available")
    device: str = Field(..., description="Current device being used")


class ModelInfo(BaseModel):
    """Model information."""

    name: str = Field(..., description="Model name")
    asr_type: str = Field(..., description="ASR type: 'aed' or 'llm'")
    status: str = Field(..., description="Model status: 'loaded', 'loading', 'error'")


class ModelsResponse(BaseModel):
    """Models list response."""

    models: List[ModelInfo] = Field(..., description="List of available models")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
