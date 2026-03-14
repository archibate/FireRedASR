# FireRedASR-LLM-L Usage Guide

FireRedASR-LLM-L is a Large Language Model (LLM) based Chinese speech recognition system with state-of-the-art Chinese recognition capabilities.

## System Requirements

- **GPU**: NVIDIA RTX A6000 (48GB) or equivalent
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.10
- **CUDA**: CUDA 12.x support

## Quick Start

### 1. Activate Environment

```bash
conda activate fireredasr
cd /home/ubuntu/FireRedASR
export PYTHONPATH=/home/ubuntu/FireRedASR:$PYTHONPATH
```

### 2. Run Speech Recognition

**Single file:**
```bash
CUDA_VISIBLE_DEVICES=0 python fireredasr/speech2text.py \
    --asr_type "llm" \
    --model_dir pretrained_models/FireRedASR-LLM-L \
    --wav_path /path/to/your/audio.wav \
    --output out/result.txt
```

**Multiple files (method 1: specify files):**
```bash
CUDA_VISIBLE_DEVICES=0 python fireredasr/speech2text.py \
    --asr_type "llm" \
    --model_dir pretrained_models/FireRedASR-LLM-L \
    --wav_paths audio1.wav audio2.wav audio3.wav \
    --output out/results.txt
```

**Multiple files (method 2: specify directory):**
```bash
CUDA_VISIBLE_DEVICES=0 python fireredasr/speech2text.py \
    --asr_type "llm" \
    --model_dir pretrained_models/FireRedASR-LLM-L \
    --wav_dir /path/to/wav/directory/ \
    --output out/results.txt
```

**Multiple files (method 3: use scp file):**
```bash
# Create wav.scp file, format: uttid wav_path
# BAC009S0764W0121 /path/to/audio1.wav
# IT0011W0001 /path/to/audio2.wav

CUDA_VISIBLE_DEVICES=0 python fireredasr/speech2text.py \
    --asr_type "llm" \
    --model_dir pretrained_models/FireRedASR-LLM-L \
    --wav_scp wav.scp \
    --output out/results.txt
```

## Audio Format Requirements

**Required specifications:**
- Sample rate: 16kHz
- Bit depth: 16-bit
- Channels: Mono
- Format: PCM WAV

**Convert audio using ffmpeg:**
```bash
# Install ffmpeg (if not installed)
sudo apt-get install ffmpeg

# Convert audio format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -sample_fmt s16 output.wav
```

## Important Limitations

- **Maximum audio length**: 30 seconds
- Audio longer than 30 seconds must be split before recognition

## Parameter Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--asr_type` | - | Must be set to `"llm"` for LLM version |
| `--model_dir` | - | Model directory path |
| `--wav_path` | - | Single audio file path |
| `--wav_paths` | - | Multiple audio file paths (space-separated) |
| `--wav_dir` | - | Audio files directory |
| `--wav_scp` | - | scp format audio list file |
| `--output` | - | Output result file path |
| `--use_gpu` | 1 | Use GPU (0/1) |
| `--batch_size` | 1 | Batch size |
| `--beam_size` | 3 | Beam search size |
| `--repetition_penalty` | 3.0 | Repetition penalty coefficient |
| `--llm_length_penalty` | 1.0 | Length penalty coefficient |
| `--temperature` | 1.0 | Sampling temperature |

## Output Format

Output file contains one result per line in JSON format:
```json
{'uttid': 'BAC009S0764W0121', 'text': '甚至出现交易几乎停滞的情况', 'wav': 'audio.wav', 'rtf': '0.2530'}
```

Field descriptions:
- `uttid`: Audio filename (without extension)
- `text`: Recognition result text
- `wav`: Audio file path
- `rtf`: Real-Time Factor (< 1.0 means faster than real-time)

## Python API Usage

```python
import sys
sys.path.insert(0, '/home/ubuntu/FireRedASR')

from fireredasr.models.fireredasr import FireRedAsr

# Load model
model = FireRedAsr.from_pretrained(
    "llm",
    "/home/ubuntu/FireRedASR/pretrained_models/FireRedASR-LLM-L"
)

# Transcribe audio
result = model.transcribe(
    wav_path="/path/to/audio.wav",
    batch_size=1,
    beam_size=3,
    repetition_penalty=3.0,
    llm_length_penalty=1.0,
    temperature=1.0
)

print(result['text'])
```

## Model File Structure

```
pretrained_models/FireRedASR-LLM-L/
├── model.pth.tar          # ASR model weights (LoRA adapter)
├── asr_encoder.pth.tar    # Speech encoder weights
├── cmvn.ark               # CMVN parameters
├── cmvn.txt               # CMVN parameters (text format)
├── config.yaml            # Configuration file
├── configuration.json     # Metadata
└── Qwen2-7B-Instruct/     # Base LLM model
    ├── config.json
    ├── model-00001-of-00004.safetensors
    ├── model-00002-of-00004.safetensors
    ├── model-00003-of-00004.safetensors
    ├── model-00004-of-00004.safetensors
    ├── tokenizer.json
    └── ...
```

## Performance Metrics

- **Model Parameters**: 8.3B (161M trainable)
- **RTF**: ~0.25 (RTX A6000)
- **VRAM Usage**: ~16GB

## Troubleshooting

### Q: What if audio exceeds 30 seconds?
A: Split the audio into segments ≤30 seconds before recognition.

### Q: How to improve recognition speed?
A: Try:
- Reduce `beam_size` (may decrease accuracy)
- Use smaller `batch_size`

### Q: Recognition results are poor?
A: Try adjusting these parameters:
- Increase `beam_size` (e.g., 5)
- Adjust `repetition_penalty` (e.g., 2.0-4.0)
- Adjust `temperature` (e.g., 0.8-1.2)

### Q: Out of memory?
A: Try:
- Use smaller batch_size
- Consider using FireRedASR-AED (non-LLM version, lower VRAM requirement)

## Links

- [GitHub Repository](https://github.com/FireRedTeam/FireRedASR)
- [ModelScope Model](https://www.modelscope.cn/FireRedTeam/FireRedASR-LLM-L)
- [Qwen2-7B-Instruct](https://huggingface.co/Qwen/Qwen2-7B-Instruct)
