# FireRedASR API

A RESTful API service for [FireRedASR](https://github.com/FireRedTeam/FireRedASR) speech recognition.

## Features

- RESTful API for speech-to-text transcription
- Support for single file and batch transcription
- Automatic audio format conversion (WAV, MP3, M4A, etc.)
- API key authentication
- GPU acceleration support
- Interactive API documentation (Swagger UI)

## Quick Start

### 1. Prerequisites

- Python 3.10+
- CUDA 11.0+ (for GPU support)
- ffmpeg (for audio conversion)

### 2. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/FireRedTeam/FireRedASR.git
cd FireRedASR

# Create conda environment
conda create --name fireredasr python=3.10
conda activate fireredasr

# Install dependencies
pip install -r requirements.txt
```

### 3. Download Models

Download model weights from [Hugging Face](https://huggingface.co/fireredteam):

**FireRedASR-AED-L** (faster, smaller):
```bash
# Download and place in pretrained_models/FireRedASR-AED-L
```

**FireRedASR-LLM-L** (better accuracy, requires Qwen2-7B):
```bash
# Download FireRedASR-LLM-L and Qwen2-7B-Instruct
# Place both in pretrained_models/
cd pretrained_models/FireRedASR-LLM-L
ln -s ../Qwen2-7B-Instruct
```

### 4. Start the Server

```bash
# Using the startup script (recommended)
./scripts/start_server.sh

# Or directly with Python
python -m api.main
```

The API will be available at `http://localhost:8000`.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ASR_TYPE` | `llm` | Model type: `aed` or `llm` |
| `MODEL_DIR` | `pretrained_models/FireRedASR-LLM-L` | Path to model directory |
| `DEVICE` | `cuda` | Device: `cuda` or `cpu` |
| `API_KEYS` | `""` | Comma-separated API keys |

### Command Line Options

```bash
./scripts/start_server.sh --help

# Custom port and API key
./scripts/start_server.sh --port 8080 --api-key my-secret-key

# Multiple API keys
API_KEYS=key1,key2 ./scripts/start_server.sh

# Use AED model (faster)
ASR_TYPE=aed MODEL_DIR=pretrained_models/FireRedASR-AED-L ./scripts/start_server.sh
```

## API Usage

### Authentication

Include your API key in requests (required if `API_KEYS` is configured):

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/v1/models
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (no auth) |
| GET | `/v1/models` | List available models |
| POST | `/v1/transcribe` | Transcribe single audio file |
| POST | `/v1/transcribe/batch` | Transcribe multiple files |

### Examples

**Health Check**
```bash
curl http://localhost:8000/health
```

**Transcribe Audio**
```bash
curl -X POST http://localhost:8000/v1/transcribe \
  -H "X-API-Key: your-api-key" \
  -F "audio=@test.wav"
```

**Batch Transcription**
```bash
curl -X POST http://localhost:8000/v1/transcribe/batch \
  -H "X-API-Key: your-api-key" \
  -F "audios=@file1.wav" \
  -F "audios=@file2.mp3"
```

**Python Client**
```python
import requests

API_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": "your-api-key"}

with open("audio.wav", "rb") as f:
    response = requests.post(
        f"{API_URL}/v1/transcribe",
        headers=HEADERS,
        files={"audio": f}
    )
    print(response.json())
```

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

ENV ASR_TYPE=llm
ENV DEVICE=cuda

EXPOSE 8000
CMD ["python", "-m", "api.main"]
```

```bash
docker build -t fireredasr-api .
docker run -d -p 8000:8000 --gpus all \
  -v /path/to/models:/app/pretrained_models \
  -e API_KEYS=your-key \
  fireredasr-api
```

### Production with Gunicorn

```bash
pip install gunicorn

gunicorn api.main:app \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

### Systemd Service

Create `/etc/systemd/system/fireredasr-api.service`:

```ini
[Unit]
Description=FireRedASR API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/FireRedASR
Environment="ASR_TYPE=llm"
Environment="API_KEYS=your-key"
ExecStart=/path/to/conda/envs/fireredasr/bin/python -m api.main
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fireredasr-api
sudo systemctl start fireredasr-api
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Detailed Reference**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

## Limitations

| Model | Max Audio Duration | Notes |
|-------|-------------------|-------|
| FireRedASR-AED | 60s | Longer audio may cause hallucination |
| FireRedASR-LLM | 30s | Recommended limit |

## Troubleshooting

**Model not found**
```
Error: Model directory not found: pretrained_models/FireRedASR-LLM-L
```
Download model weights and verify `MODEL_DIR` path.

**CUDA out of memory**
Use CPU or reduce batch size:
```bash
DEVICE=cpu ./scripts/start_server.sh
```

**ffmpeg not found**
Install ffmpeg:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

## License

Same as [FireRedASR](https://github.com/FireRedTeam/FireRedASR).
