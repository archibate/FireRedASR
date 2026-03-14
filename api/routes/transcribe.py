"""Transcription API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from api.middleware.auth import require_api_key
from api.models.schemas import (
    BatchTranscriptionResult,
    ErrorResponse,
    HealthResponse,
    ModelInfo,
    ModelsResponse,
    TranscriptionResult,
)
from api.services.asr_service import asr_service
from api.services.audio_utils import (
    AudioTooLongError,
    AudioValidationError,
    process_audio_upload,
)
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint (no authentication required).

    Returns service health status including model and GPU availability.
    """
    import torch

    return HealthResponse(
        status="healthy" if asr_service.is_loaded else "unhealthy",
        model_loaded=asr_service.is_loaded,
        gpu_available=torch.cuda.is_available(),
        device=settings.device,
    )


@router.get("/v1/models", response_model=ModelsResponse)
async def list_models(request: Request):
    """
    List available models and their status.

    Requires API key authentication.
    """
    require_api_key(request)

    status = "loaded" if asr_service.is_loaded else "loading" if asr_service.is_loading else "error"

    return ModelsResponse(
        models=[
            ModelInfo(
                name=settings.model_dir,
                asr_type=settings.asr_type,
                status=status,
            )
        ]
    )


@router.post(
    "/v1/transcribe",
    response_model=TranscriptionResult,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def transcribe(
    request: Request,
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, M4A, etc.)"),
    beam_size: int = Form(default=settings.default_beam_size, description="Beam size for decoding"),
    repetition_penalty: float = Form(
        default=settings.default_repetition_penalty,
        description="Repetition penalty (LLM only)",
    ),
    decode_max_len: int = Form(default=0, description="Maximum decode length (0 for auto)"),
    decode_min_len: int = Form(default=0, description="Minimum decode length (LLM only)"),
    temperature: float = Form(default=1.0, description="Temperature for sampling (LLM only)"),
    llm_length_penalty: float = Form(default=0.0, description="Length penalty (LLM only)"),
    nbest: int = Form(default=1, description="Number of best hypotheses (AED only)"),
    softmax_smoothing: float = Form(default=1.0, description="Softmax smoothing (AED only)"),
    aed_length_penalty: float = Form(default=0.0, description="Length penalty (AED only)"),
    eos_penalty: float = Form(default=1.0, description="EOS penalty (AED only)"),
):
    """
    Transcribe a single audio file.

    Accepts audio files in various formats (WAV, MP3, M4A, etc.) and returns
    the recognized text. Audio is automatically converted to 16kHz mono WAV.

    Requires API key authentication via X-API-Key header.
    """
    require_api_key(request)

    # Check if model is loaded
    if not asr_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please wait for model initialization.",
        )

    try:
        # Read uploaded file
        audio_bytes = await audio.read()
        filename = audio.filename or "audio.wav"

        # Process audio (validate/convert format)
        try:
            wav_bytes, _ = process_audio_upload(
                audio_bytes, filename, settings.max_audio_duration
            )
        except AudioTooLongError as e:
            raise HTTPException(status_code=413, detail=str(e))
        except AudioValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Run transcription
        result = asr_service.transcribe(
            wav_bytes,
            beam_size=beam_size,
            repetition_penalty=repetition_penalty,
            decode_max_len=decode_max_len,
            decode_min_len=decode_min_len,
            temperature=temperature,
            llm_length_penalty=llm_length_penalty,
            nbest=nbest,
            softmax_smoothing=softmax_smoothing,
            aed_length_penalty=aed_length_penalty,
            eos_penalty=eos_penalty,
        )

        return TranscriptionResult(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post(
    "/v1/transcribe/batch",
    response_model=BatchTranscriptionResult,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def transcribe_batch(
    request: Request,
    audios: List[UploadFile] = File(..., description="Multiple audio files"),
    beam_size: int = Form(default=settings.default_beam_size, description="Beam size for decoding"),
    repetition_penalty: float = Form(
        default=settings.default_repetition_penalty,
        description="Repetition penalty (LLM only)",
    ),
    decode_max_len: int = Form(default=0, description="Maximum decode length (0 for auto)"),
    decode_min_len: int = Form(default=0, description="Minimum decode length (LLM only)"),
    temperature: float = Form(default=1.0, description="Temperature for sampling (LLM only)"),
    llm_length_penalty: float = Form(default=0.0, description="Length penalty (LLM only)"),
    nbest: int = Form(default=1, description="Number of best hypotheses (AED only)"),
    softmax_smoothing: float = Form(default=1.0, description="Softmax smoothing (AED only)"),
    aed_length_penalty: float = Form(default=0.0, description="Length penalty (AED only)"),
    eos_penalty: float = Form(default=1.0, description="EOS penalty (AED only)"),
):
    """
    Transcribe multiple audio files in batch.

    Accepts multiple audio files and returns transcription results for each.
    Maximum batch size is configurable (default: 8).

    Requires API key authentication via X-API-Key header.
    """
    require_api_key(request)

    # Check if model is loaded
    if not asr_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please wait for model initialization.",
        )

    # Check batch size
    if len(audios) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(audios)} exceeds maximum {settings.max_batch_size}",
        )

    try:
        wav_bytes_list = []
        durations = []

        # Process all uploaded files
        for audio in audios:
            audio_bytes = await audio.read()
            filename = audio.filename or "audio.wav"

            try:
                wav_bytes, duration = process_audio_upload(
                    audio_bytes, filename, settings.max_audio_duration
                )
                wav_bytes_list.append(wav_bytes)
                durations.append(duration)
            except AudioTooLongError as e:
                raise HTTPException(status_code=413, detail=str(e))
            except AudioValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Run batch transcription
        results = asr_service.transcribe_batch(
            wav_bytes_list,
            beam_size=beam_size,
            repetition_penalty=repetition_penalty,
            decode_max_len=decode_max_len,
            decode_min_len=decode_min_len,
            temperature=temperature,
            llm_length_penalty=llm_length_penalty,
            nbest=nbest,
            softmax_smoothing=softmax_smoothing,
            aed_length_penalty=aed_length_penalty,
            eos_penalty=eos_penalty,
        )

        return BatchTranscriptionResult(
            results=[TranscriptionResult(**r) for r in results]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch transcription failed: {str(e)}")
