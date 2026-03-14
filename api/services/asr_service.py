"""ASR Service - Singleton service for model management and inference."""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

import torch

from api.config import settings

logger = logging.getLogger(__name__)


class ASRService:
    """Singleton service for ASR model management and inference."""

    _instance: Optional["ASRService"] = None
    _model = None
    _loaded: bool = False
    _loading: bool = False
    _error: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded

    @property
    def is_loading(self) -> bool:
        """Check if model is currently loading."""
        return self._loading

    @property
    def error(self) -> Optional[str]:
        """Get last error message."""
        return self._error

    @property
    def gpu_available(self) -> bool:
        """Check if GPU is available."""
        return torch.cuda.is_available()

    def load_model(self) -> None:
        """Load the ASR model."""
        if self._loaded or self._loading:
            return

        self._loading = True
        self._error = None

        try:
            logger.info(f"Loading FireRedASR model (type={settings.asr_type})...")
            logger.info(f"Model directory: {settings.model_dir}")

            # Import here to avoid loading at module level
            from fireredasr.models.fireredasr import FireRedAsr

            # Check model directory exists
            if not os.path.exists(settings.model_dir):
                raise FileNotFoundError(
                    f"Model directory not found: {settings.model_dir}"
                )

            # Load model
            start_time = time.time()
            self._model = FireRedAsr.from_pretrained(
                settings.asr_type, settings.model_dir
            )

            # Move to GPU if requested
            if settings.use_gpu and torch.cuda.is_available():
                self._model.model.cuda()
                logger.info("Model moved to GPU")
            else:
                self._model.model.cpu()
                logger.info("Model using CPU")

            elapsed = time.time() - start_time
            logger.info(f"Model loaded successfully in {elapsed:.2f}s")

            self._loaded = True
            self._loading = False

        except Exception as e:
            self._loading = False
            self._error = str(e)
            logger.error(f"Failed to load model: {e}")
            raise

    def transcribe(
        self,
        audio_bytes: bytes,
        beam_size: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        decode_max_len: Optional[int] = None,
        decode_min_len: Optional[int] = None,
        temperature: Optional[float] = None,
        llm_length_penalty: Optional[float] = None,
        # AED-specific parameters
        nbest: Optional[int] = None,
        softmax_smoothing: Optional[float] = None,
        aed_length_penalty: Optional[float] = None,
        eos_penalty: Optional[float] = None,
    ) -> Dict:
        """
        Transcribe audio bytes.

        Args:
            audio_bytes: WAV audio bytes (16kHz, mono, 16-bit)
            beam_size: Beam size for decoding
            repetition_penalty: Repetition penalty (LLM only)
            decode_max_len: Maximum decode length
            decode_min_len: Minimum decode length (LLM only)
            temperature: Temperature for sampling (LLM only)
            llm_length_penalty: Length penalty (LLM only)
            nbest: Number of best hypotheses (AED only)
            softmax_smoothing: Softmax smoothing (AED only)
            aed_length_penalty: Length penalty (AED only)
            eos_penalty: EOS penalty (AED only)

        Returns:
            Dict with 'text', 'rtf', 'duration_seconds'
        """
        if not self._loaded or self._model is None:
            raise RuntimeError("Model not loaded")

        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Get audio duration using soundfile
            import soundfile as sf

            info = sf.info(tmp_path)
            duration = info.duration

            # Build transcription args
            args = {
                "use_gpu": settings.use_gpu and torch.cuda.is_available(),
                "beam_size": beam_size or settings.default_beam_size,
                "decode_max_len": decode_max_len or settings.default_decode_max_len,
            }

            # Add model-specific parameters
            if settings.asr_type == "llm":
                args["repetition_penalty"] = (
                    repetition_penalty or settings.default_repetition_penalty
                )
                args["decode_min_len"] = (
                    decode_min_len or settings.default_decode_min_len
                )
                args["temperature"] = temperature or settings.default_temperature
                args["llm_length_penalty"] = (
                    llm_length_penalty or settings.default_llm_length_penalty
                )
            else:  # aed
                args["nbest"] = nbest or settings.default_nbest
                args["softmax_smoothing"] = (
                    softmax_smoothing or settings.default_softmax_smoothing
                )
                args["aed_length_penalty"] = (
                    aed_length_penalty or settings.default_aed_length_penalty
                )
                args["eos_penalty"] = eos_penalty or settings.default_eos_penalty

            # Run transcription
            uttid = "audio"
            results = self._model.transcribe([uttid], [tmp_path], args)

            if not results:
                raise RuntimeError("Transcription returned no results")

            result = results[0]

            return {
                "text": result["text"],
                "rtf": float(result["rtf"]),
                "duration_seconds": duration,
            }

        finally:
            # Cleanup temp file
            Path(tmp_path).unlink(missing_ok=True)

    def transcribe_batch(
        self,
        audio_bytes_list: List[bytes],
        beam_size: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        decode_max_len: Optional[int] = None,
        decode_min_len: Optional[int] = None,
        temperature: Optional[float] = None,
        llm_length_penalty: Optional[float] = None,
        # AED-specific parameters
        nbest: Optional[int] = None,
        softmax_smoothing: Optional[float] = None,
        aed_length_penalty: Optional[float] = None,
        eos_penalty: Optional[float] = None,
    ) -> List[Dict]:
        """
        Transcribe multiple audio files.

        Args:
            audio_bytes_list: List of WAV audio bytes
            Other args same as transcribe()

        Returns:
            List of dicts with 'text', 'rtf', 'duration_seconds'
        """
        if not self._loaded or self._model is None:
            raise RuntimeError("Model not loaded")

        if len(audio_bytes_list) > settings.max_batch_size:
            raise ValueError(
                f"Batch size {len(audio_bytes_list)} exceeds maximum {settings.max_batch_size}"
            )

        # Save all audio to temp files
        tmp_paths = []
        durations = []

        try:
            import soundfile as sf

            for audio_bytes in audio_bytes_list:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name
                    tmp_paths.append(tmp_path)

                    info = sf.info(tmp_path)
                    durations.append(info.duration)

            # Build transcription args
            args = {
                "use_gpu": settings.use_gpu and torch.cuda.is_available(),
                "beam_size": beam_size or settings.default_beam_size,
                "decode_max_len": decode_max_len or settings.default_decode_max_len,
            }

            if settings.asr_type == "llm":
                args["repetition_penalty"] = (
                    repetition_penalty or settings.default_repetition_penalty
                )
                args["decode_min_len"] = (
                    decode_min_len or settings.default_decode_min_len
                )
                args["temperature"] = temperature or settings.default_temperature
                args["llm_length_penalty"] = (
                    llm_length_penalty or settings.default_llm_length_penalty
                )
            else:
                args["nbest"] = nbest or settings.default_nbest
                args["softmax_smoothing"] = (
                    softmax_smoothing or settings.default_softmax_smoothing
                )
                args["aed_length_penalty"] = (
                    aed_length_penalty or settings.default_aed_length_penalty
                )
                args["eos_penalty"] = eos_penalty or settings.default_eos_penalty

            # Generate uttids
            uttids = [f"audio_{i}" for i in range(len(tmp_paths))]

            # Run batch transcription
            results = self._model.transcribe(uttids, tmp_paths, args)

            # Format results
            formatted_results = []
            for i, result in enumerate(results):
                formatted_results.append(
                    {
                        "text": result["text"],
                        "rtf": float(result["rtf"]),
                        "duration_seconds": durations[i],
                    }
                )

            return formatted_results

        finally:
            # Cleanup temp files
            for tmp_path in tmp_paths:
                Path(tmp_path).unlink(missing_ok=True)


# Global service instance
asr_service = ASRService()
