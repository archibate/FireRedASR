#!/bin/bash
# Start FireRedASR API server
#
# Usage:
#   ./scripts/start_server.sh [OPTIONS]
#
# Options:
#   --port PORT          Server port (default: 8000)
#   --host HOST          Server host (default: 0.0.0.0)
#   --workers N          Number of workers (default: 1)
#   --api-key KEY        API key for authentication (can be repeated)
#
# Environment variables:
#   ASR_TYPE             ASR type: "aed" or "llm" (default: llm)
#   MODEL_DIR            Model directory path (default: pretrained_models/FireRedASR-LLM-L)
#   DEVICE               Device: "cuda" or "cpu" (default: cuda)
#   API_KEYS             Comma-separated API keys
#
# Example:
#   API_KEYS=key1,key2 ./scripts/start_server.sh --port 8080

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
TIMEOUT="${TIMEOUT:-300}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --api-key)
            if [ -z "$API_KEYS" ]; then
                API_KEYS="$2"
            else
                API_KEYS="${API_KEYS},$2"
            fi
            shift 2
            ;;
        --help)
            head -30 "$0" | tail -28
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Change to project directory
cd "$PROJECT_DIR"

# Export environment variables for the app
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"

# Set defaults if not provided
export ASR_TYPE="${ASR_TYPE:-llm}"
export MODEL_DIR="${MODEL_DIR:-pretrained_models/FireRedASR-LLM-L}"
export DEVICE="${DEVICE:-cuda}"
export API_KEYS="${API_KEYS:-}"

echo "=========================================="
echo "Starting FireRedASR API Server"
echo "=========================================="
echo "Project dir:  $PROJECT_DIR"
echo "ASR type:     $ASR_TYPE"
echo "Model dir:    $MODEL_DIR"
echo "Device:       $DEVICE"
echo "Host:         $HOST"
echo "Port:         $PORT"
echo "Workers:      $WORKERS"
echo "API keys:     $([ -n "$API_KEYS" ] && echo "configured" || echo "none")"
echo "=========================================="

# Check if conda environment is active
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Warning: No conda environment detected."
    echo "Consider running: conda activate fireredasr"
fi

# Check if model directory exists
if [ ! -d "$MODEL_DIR" ]; then
    echo "Error: Model directory not found: $MODEL_DIR"
    exit 1
fi

# Start uvicorn server
exec python -m uvicorn api.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --timeout-keep-alive "$TIMEOUT"
