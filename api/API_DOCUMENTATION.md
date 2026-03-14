# FireRedASR API Documentation

A RESTful API for FireRedASR speech recognition service.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [List Models](#list-models)
  - [Transcribe Audio](#transcribe-audio)
  - [Batch Transcription](#batch-transcription)
- [Response Schemas](#response-schemas)
- [Error Handling](#error-handling)
- [Configuration](#configuration)
- [Examples](#examples)

---

## Overview

FireRedASR API provides speech-to-text transcription capabilities using FireRedASR models (AED or LLM variants). The API supports:

- Single file transcription
- Batch transcription (up to 8 files)
- Multiple audio formats (WAV, MP3, M4A, etc.)
- Automatic audio conversion to 16kHz mono
- GPU acceleration support

---

## Authentication

All endpoints except `/health` require API key authentication.

Include your API key in the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

If no API keys are configured on the server, authentication is disabled.

---

## Base URL

```
http://localhost:8000
```

Interactive documentation available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

---

## Endpoints

### Health Check

Check service health status (no authentication required).

**Request**
```http
GET /health
```

**Response**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": true,
  "device": "cuda"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service status: `healthy` or `unhealthy` |
| `model_loaded` | boolean | Whether the ASR model is loaded |
| `gpu_available` | boolean | Whether GPU is available |
| `device` | string | Current device: `cuda` or `cpu` |

---

### List Models

List available models and their status.

**Request**
```http
GET /v1/models
Headers:
  X-API-Key: your-api-key
```

**Response**
```json
{
  "models": [
    {
      "name": "pretrained_models/FireRedASR-LLM-L",
      "asr_type": "llm",
      "status": "loaded"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `models` | array | List of available models |
| `models[].name` | string | Model directory path |
| `models[].asr_type` | string | ASR type: `aed` or `llm` |
| `models[].status` | string | Model status: `loaded`, `loading`, or `error` |

---

### Transcribe Audio

Transcribe a single audio file.

**Request**
```http
POST /v1/transcribe
Headers:
  X-API-Key: your-api-key
  Content-Type: multipart/form-data
```

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `audio` | file | Yes | - | Audio file (WAV, MP3, M4A, etc.) |
| `beam_size` | int | No | 3 | Beam size for decoding |
| `decode_max_len` | int | No | 0 | Maximum decode length (0 = auto) |

**LLM-specific Parameters** (only for `asr_type=llm`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repetition_penalty` | float | 3.0 | Repetition penalty |
| `decode_min_len` | int | 0 | Minimum decode length |
| `temperature` | float | 1.0 | Temperature for sampling |
| `llm_length_penalty` | float | 0.0 | Length penalty |

**AED-specific Parameters** (only for `asr_type=aed`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nbest` | int | 1 | Number of best hypotheses |
| `softmax_smoothing` | float | 1.0 | Softmax smoothing |
| `aed_length_penalty` | float | 0.0 | Length penalty |
| `eos_penalty` | float | 1.0 | EOS penalty |

**Response**
```json
{
  "text": "Hello world, this is a transcription.",
  "rtf": 0.15,
  "duration_seconds": 3.5
}
```

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Recognized text |
| `rtf` | float | Real-time factor (processing time / audio duration) |
| `duration_seconds` | float | Audio duration in seconds |

**Constraints**
- Maximum audio duration: 30 seconds (configurable)
- Supported formats: WAV, MP3, M4A, and any format supported by ffmpeg

---

### Batch Transcription

Transcribe multiple audio files in a single request.

**Request**
```http
POST /v1/transcribe/batch
Headers:
  X-API-Key: your-api-key
  Content-Type: multipart/form-data
```

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `audios` | file[] | Yes | - | Multiple audio files |
| ... | ... | No | ... | Same parameters as single transcription |

**Response**
```json
{
  "results": [
    {
      "text": "First transcription.",
      "rtf": 0.12,
      "duration_seconds": 2.1
    },
    {
      "text": "Second transcription.",
      "rtf": 0.14,
      "duration_seconds": 3.2
    }
  ]
}
```

**Constraints**
- Maximum batch size: 8 files (configurable)
- Each file must not exceed maximum duration

---

## Response Schemas

### TranscriptionResult
```json
{
  "text": "string",
  "rtf": "float",
  "duration_seconds": "float"
}
```

### BatchTranscriptionResult
```json
{
  "results": ["TranscriptionResult[]"]
}
```

### HealthResponse
```json
{
  "status": "string",
  "model_loaded": "boolean",
  "gpu_available": "boolean",
  "device": "string"
}
```

### ModelsResponse
```json
{
  "models": [
    {
      "name": "string",
      "asr_type": "string",
      "status": "string"
    }
  ]
}
```

### ErrorResponse
```json
{
  "error": "string",
  "detail": "string | null"
}
```

---

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad request (invalid audio format) |
| 401 | Unauthorized (missing or invalid API key) |
| 413 | Payload too large (audio exceeds max duration) |
| 500 | Internal server error |
| 503 | Service unavailable (model not loaded) |

**Example Error Response**
```json
{
  "detail": "Audio duration 45.00s exceeds maximum 30s"
}
```

---

## Configuration

Environment variables can be set via `.env` file or system environment:

### Model Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `asr_type` | `llm` | ASR model type: `aed` or `llm` |
| `model_dir` | `pretrained_models/FireRedASR-LLM-L` | Path to model directory |
| `device` | `cuda` | Device to use: `cuda` or `cpu` |

### Audio Constraints

| Variable | Default | Description |
|----------|---------|-------------|
| `max_audio_duration` | `30` | Maximum audio duration in seconds |
| `max_batch_size` | `8` | Maximum files per batch request |

### Decoding Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `default_beam_size` | `3` | Default beam size |
| `default_repetition_penalty` | `3.0` | Default repetition penalty (LLM) |
| `default_decode_max_len` | `0` | Default max decode length (0 = auto) |
| `default_decode_min_len` | `0` | Default min decode length (LLM) |
| `default_temperature` | `1.0` | Default temperature (LLM) |
| `default_llm_length_penalty` | `0.0` | Default length penalty (LLM) |
| `default_nbest` | `1` | Default nbest (AED) |
| `default_softmax_smoothing` | `1.0` | Default softmax smoothing (AED) |
| `default_aed_length_penalty` | `0.0` | Default length penalty (AED) |
| `default_eos_penalty` | `1.0` | Default EOS penalty (AED) |

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `host` | `0.0.0.0` | Server host |
| `port` | `8000` | Server port |
| `workers` | `1` | Number of workers |
| `timeout_keep_alive` | `300` | Keep-alive timeout |
| `api_keys` | `""` | Comma-separated API keys |

---

## Examples

### cURL

**Health Check**
```bash
curl http://localhost:8000/health
```

**Single Transcription**
```bash
curl -X POST http://localhost:8000/v1/transcribe \
  -H "X-API-Key: your-api-key" \
  -F "audio=@test.wav"
```

**With Parameters**
```bash
curl -X POST http://localhost:8000/v1/transcribe \
  -H "X-API-Key: your-api-key" \
  -F "audio=@test.mp3" \
  -F "beam_size=5" \
  -F "temperature=0.8"
```

**Batch Transcription**
```bash
curl -X POST http://localhost:8000/v1/transcribe/batch \
  -H "X-API-Key: your-api-key" \
  -F "audios=@file1.wav" \
  -F "audios=@file2.wav" \
  -F "audios=@file3.mp3"
```

### Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"
HEADERS = {"X-API-Key": API_KEY}

# Health check
response = requests.get(f"{API_URL}/health")
print(response.json())

# Single transcription
with open("audio.wav", "rb") as f:
    files = {"audio": f}
    data = {"beam_size": 5}
    response = requests.post(
        f"{API_URL}/v1/transcribe",
        headers=HEADERS,
        files=files,
        data=data
    )
    print(response.json())

# Batch transcription
files = [
    ("audios", open("file1.wav", "rb")),
    ("audios", open("file2.mp3", "rb")),
]
response = requests.post(
    f"{API_URL}/v1/transcribe/batch",
    headers=HEADERS,
    files=files
)
print(response.json())
for f in files:
    f[1].close()
```

### JavaScript (Fetch)

```javascript
const API_URL = "http://localhost:8000";
const API_KEY = "your-api-key";

// Single transcription
async function transcribe(file) {
  const formData = new FormData();
  formData.append("audio", file);
  formData.append("beam_size", "5");

  const response = await fetch(`${API_URL}/v1/transcribe`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
    },
    body: formData,
  });

  return response.json();
}

// Usage
const input = document.querySelector('input[type="file"]');
const result = await transcribe(input.files[0]);
console.log(result.text);
```

---

## Running the Server

```bash
# Using Python
python -m api.main

# Using uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000

# With environment variables
ASR_TYPE=llm DEVICE=cuda python -m api.main
```
