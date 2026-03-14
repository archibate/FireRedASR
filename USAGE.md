# FireRedASR-LLM-L 使用指南

FireRedASR-LLM-L 是一个基于大语言模型（LLM）的中文语音识别系统，具有顶尖的中文识别能力。

## 系统要求

- **GPU**: NVIDIA RTX A6000 (48GB) 或同等显存的显卡
- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **Python**: 3.10
- **CUDA**: 支持 CUDA 12.x

## 快速开始

### 1. 激活环境

```bash
conda activate fireredasr
cd /home/ubuntu/FireRedASR
export PYTHONPATH=/home/ubuntu/FireRedASR:$PYTHONPATH
```

### 2. 运行语音识别

**单文件识别：**
```bash
CUDA_VISIBLE_DEVICES=0 python fireredasr/speech2text.py \
    --asr_type "llm" \
    --model_dir pretrained_models/FireRedASR-LLM-L \
    --wav_path /path/to/your/audio.wav \
    --output out/result.txt
```

**多文件识别（方式一：指定多个文件）：**
```bash
CUDA_VISIBLE_DEVICES=0 python fireredasr/speech2text.py \
    --asr_type "llm" \
    --model_dir pretrained_models/FireRedASR-LLM-L \
    --wav_paths audio1.wav audio2.wav audio3.wav \
    --output out/results.txt
```

**多文件识别（方式二：指定目录）：**
```bash
CUDA_VISIBLE_DEVICES=0 python fireredasr/speech2text.py \
    --asr_type "llm" \
    --model_dir pretrained_models/FireRedASR-LLM-L \
    --wav_dir /path/to/wav/directory/ \
    --output out/results.txt
```

**多文件识别（方式三：使用 scp 文件）：**
```bash
# 创建 wav.scp 文件，格式：uttid wav_path
# BAC009S0764W0121 /path/to/audio1.wav
# IT0011W0001 /path/to/audio2.wav

CUDA_VISIBLE_DEVICES=0 python fireredasr/speech2text.py \
    --asr_type "llm" \
    --model_dir pretrained_models/FireRedASR-LLM-L \
    --wav_scp wav.scp \
    --output out/results.txt
```

## 音频格式要求

**必须满足以下条件：**
- 采样率：16kHz
- 位深：16-bit
- 声道：单声道 (Mono)
- 格式：PCM WAV

**使用 ffmpeg 转换音频：**
```bash
# 安装 ffmpeg（如果未安装）
sudo apt-get install ffmpeg

# 转换音频格式
ffmpeg -i input.mp3 -ar 16000 -ac 1 -sample_fmt s16 output.wav
```

## 重要限制

- **最大音频长度**: 30秒
- 超过30秒的音频需要手动切分后再进行识别

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--asr_type` | - | 必须设为 `"llm"` 使用 LLM 版本 |
| `--model_dir` | - | 模型目录路径 |
| `--wav_path` | - | 单个音频文件路径 |
| `--wav_paths` | - | 多个音频文件路径（空格分隔） |
| `--wav_dir` | - | 音频文件目录 |
| `--wav_scp` | - | scp 格式的音频列表文件 |
| `--output` | - | 输出结果文件路径 |
| `--use_gpu` | 1 | 是否使用 GPU (0/1) |
| `--batch_size` | 1 | 批处理大小 |
| `--beam_size` | 3 | 束搜索大小 |
| `--repetition_penalty` | 3.0 | 重复惩罚系数 |
| `--llm_length_penalty` | 1.0 | 长度惩罚系数 |
| `--temperature` | 1.0 | 采样温度 |

## 输出格式

输出文件每行一条结果，JSON 格式：
```json
{'uttid': 'BAC009S0764W0121', 'text': '甚至出现交易几乎停滞的情况', 'wav': 'audio.wav', 'rtf': '0.2530'}
```

字段说明：
- `uttid`: 音频文件名（不含扩展名）
- `text`: 识别结果文本
- `wav`: 音频文件路径
- `rtf`: 实时因子 (Real-Time Factor)，< 1.0 表示快于实时

## Python API 使用

```python
import sys
sys.path.insert(0, '/home/ubuntu/FireRedASR')

from fireredasr.models.fireredasr import FireRedAsr

# 加载模型
model = FireRedAsr.from_pretrained(
    "llm",
    "/home/ubuntu/FireRedASR/pretrained_models/FireRedASR-LLM-L"
)

# 识别音频
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

## 模型文件结构

```
pretrained_models/FireRedASR-LLM-L/
├── model.pth.tar          # ASR 模型权重 (LoRA adapter)
├── asr_encoder.pth.tar    # 语音编码器权重
├── cmvn.ark               # CMVN 参数
├── cmvn.txt               # CMVN 参数（文本格式）
├── config.yaml            # 配置文件
├── configuration.json     # 元数据
└── Qwen2-7B-Instruct/     # 基础 LLM 模型
    ├── config.json
    ├── model-00001-of-00004.safetensors
    ├── model-00002-of-00004.safetensors
    ├── model-00003-of-00004.safetensors
    ├── model-00004-of-00004.safetensors
    ├── tokenizer.json
    └── ...
```

## 性能指标

- **模型参数量**: 8.3B (其中 161M 为可训练参数)
- **RTF**: ~0.25 (RTX A6000)
- **显存占用**: ~16GB

## 常见问题

### Q: 音频超过30秒怎么办？
A: 需要先将音频切分为多个 ≤30秒 的片段，然后分别进行识别。

### Q: 如何提高识别速度？
A: 可以尝试：
- 减小 `beam_size`（但可能降低准确率）
- 使用更小的 `batch_size`

### Q: 识别结果不理想怎么办？
A: 可以尝试调整以下参数：
- 增大 `beam_size`（如 5）
- 调整 `repetition_penalty`（如 2.0-4.0）
- 调整 `temperature`（如 0.8-1.2）

### Q: 显存不足怎么办？
A: 可以尝试：
- 使用更小的 batch_size
- 考虑使用 FireRedASR-AED（非 LLM 版本，显存需求更低）

## 相关链接

- [GitHub 仓库](https://github.com/FireRedTeam/FireRedASR)
- [ModelScope 模型](https://www.modelscope.cn/FireRedTeam/FireRedASR-LLM-L)
- [Qwen2-7B-Instruct](https://huggingface.co/Qwen/Qwen2-7B-Instruct)
