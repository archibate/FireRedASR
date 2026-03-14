"""Audio format validation and conversion utilities."""

import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

import soundfile as sf


class AudioValidationError(Exception):
    """Raised when audio validation fails."""

    pass


class AudioTooLongError(Exception):
    """Raised when audio exceeds maximum duration."""

    pass


def get_audio_info(file_path: str) -> Tuple[int, int, int, float]:
    """
    Get audio file information.

    Returns:
        Tuple of (sample_rate, channels, bits_per_sample, duration_seconds)
    """
    info = sf.info(file_path)
    return info.samplerate, info.channels, 16, info.duration


def validate_audio_format(file_path: str, max_duration: int = 30) -> Tuple[float, int]:
    """
    Validate audio format is 16kHz, 16-bit, mono.

    Args:
        file_path: Path to audio file
        max_duration: Maximum allowed duration in seconds

    Returns:
        Tuple of (duration_seconds, sample_rate)

    Raises:
        AudioValidationError: If format is invalid
        AudioTooLongError: If audio exceeds max duration
    """
    try:
        info = sf.info(file_path)
        duration = info.duration
        sample_rate = info.samplerate
        channels = info.channels

        # Check duration
        if duration > max_duration:
            raise AudioTooLongError(
                f"Audio duration {duration:.2f}s exceeds maximum {max_duration}s"
            )

        # Check sample rate (should be 16000 after conversion)
        if sample_rate != 16000:
            raise AudioValidationError(
                f"Invalid sample rate: {sample_rate}Hz, expected 16000Hz"
            )

        # Check channels (should be mono)
        if channels != 1:
            raise AudioValidationError(
                f"Invalid channels: {channels}, expected mono (1)"
            )

        return duration, sample_rate

    except Exception as e:
        if isinstance(e, (AudioValidationError, AudioTooLongError)):
            raise
        raise AudioValidationError(f"Failed to read audio file: {str(e)}")


def convert_to_wav(
    input_bytes: bytes,
    target_sample_rate: int = 16000,
    target_channels: int = 1,
    max_duration: int = 30,
) -> Tuple[bytes, float]:
    """
    Convert audio bytes to 16kHz mono WAV format using ffmpeg.

    Args:
        input_bytes: Raw audio bytes (any format supported by ffmpeg)
        target_sample_rate: Target sample rate (default 16000)
        target_channels: Target number of channels (default 1 for mono)
        max_duration: Maximum allowed duration in seconds

    Returns:
        Tuple of (wav_bytes, duration_seconds)

    Raises:
        AudioValidationError: If conversion fails
        AudioTooLongError: If audio exceeds max duration
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
        tmp_in.write(input_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(".wav", "_converted.wav")

    try:
        # Use ffmpeg to convert to 16kHz mono WAV
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i",
            tmp_in_path,  # Input file
            "-ar",
            str(target_sample_rate),  # Sample rate
            "-ac",
            str(target_channels),  # Channels
            "-acodec",
            "pcm_s16le",  # 16-bit PCM
            "-t",
            str(max_duration + 1),  # Limit duration (with buffer)
            tmp_out_path,  # Output file
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout for conversion
        )

        if result.returncode != 0:
            raise AudioValidationError(
                f"ffmpeg conversion failed: {result.stderr}"
            )

        # Get duration of converted file
        info = sf.info(tmp_out_path)
        duration = info.duration

        # Check duration
        if duration > max_duration:
            raise AudioTooLongError(
                f"Audio duration {duration:.2f}s exceeds maximum {max_duration}s"
            )

        # Read converted file
        with open(tmp_out_path, "rb") as f:
            wav_bytes = f.read()

        return wav_bytes, duration

    except subprocess.TimeoutExpired:
        raise AudioValidationError("Audio conversion timed out")
    finally:
        # Cleanup temp files
        Path(tmp_in_path).unlink(missing_ok=True)
        Path(tmp_out_path).unlink(missing_ok=True)


def is_wav_file(file_bytes: bytes, filename: str = "") -> bool:
    """
    Check if the file is likely a WAV file.

    Args:
        file_bytes: Raw file bytes
        filename: Original filename for extension check

    Returns:
        True if likely a WAV file
    """
    # Check file extension
    if filename.lower().endswith(".wav"):
        # Also verify RIFF header
        if len(file_bytes) >= 12:
            return file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WAVE"
    return False


def process_audio_upload(
    file_bytes: bytes, filename: str, max_duration: int = 30
) -> Tuple[bytes, float]:
    """
    Process uploaded audio file - validate or convert to proper format.

    Args:
        file_bytes: Raw audio bytes
        filename: Original filename
        max_duration: Maximum allowed duration in seconds

    Returns:
        Tuple of (wav_bytes, duration_seconds)

    Raises:
        AudioValidationError: If format is invalid and conversion fails
        AudioTooLongError: If audio exceeds max duration
    """
    # Check if already a WAV file
    if is_wav_file(file_bytes, filename):
        # Save to temp file to validate
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            # Validate format
            duration, _ = validate_audio_format(tmp_path, max_duration)
            return file_bytes, duration
        except AudioValidationError:
            # WAV but wrong format - convert it
            return convert_to_wav(file_bytes, max_duration=max_duration)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    else:
        # Not a WAV file - convert using ffmpeg
        return convert_to_wav(file_bytes, max_duration=max_duration)
