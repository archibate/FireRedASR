这是为你准备的 **FireRedASR-LLM-L** 部署指南。你的 RTX A6000（48GB）是运行这个8.3B参数大模型的理想选择，可以充分发挥其顶尖的中文识别能力 。

整个部署过程主要分为以下几步：

### 🛠️ 第一步：环境配置
首先，我们需要在你的 Linux 系统（推荐 Ubuntu 20.04+）上准备好 Python 环境和代码。

1.  **克隆项目仓库**：
    ```bash
    git clone https://github.com/FireRedTeam/FireRedASR.git
    cd FireRedASR
    ```
    

2.  **创建并激活 Conda 环境**：
    建议使用 Python 3.10 来保证最佳的兼容性。
    ```bash
    conda create --name fireredasr python=3.10
    conda activate fireredasr
    ```
    

3.  **安装依赖**：
    安装项目所需的 Python 包。
    ```bash
    pip install -r requirements.txt
    ```
    

4.  **设置环境变量**：
    为了方便后续使用命令，将项目路径加入系统环境。
    ```bash
    export PATH=$PWD/fireredasr/:$PWD/fireredasr/utils/:$PATH
    export PYTHONPATH=$PWD/:$PYTHONPATH
    ```
    你可以将这两行命令添加到你的 `~/.bashrc` 文件中，这样每次登录终端都会自动设置。
    

### ⬇️ 第二步：下载模型权重
这一步是下载核心的模型文件。由于模型较大，请确保网络稳定，磁盘有充足空间。

1.  **安装 git-lfs** (如果尚未安装)：
    ```bash
    # Ubuntu/Debian
    sudo apt-get install git-lfs
    git lfs install
    ```
    

2.  **下载 FireRedASR-LLM-L 模型**：
    建议从 ModelScope 下载，速度通常更快。
    ```bash
    git clone https://www.modelscope.cn/FireRedTeam/FireRedASR-LLM-L.git
    ```
    

3.  **下载基础 LLM 权重**：
    FireRedASR-LLM-L 是基于 **Qwen2-7B-Instruct** 构建的，因此还需要单独下载这个基础模型 。
    ```bash
    # 你可以将 Qwen2-7B-Instruct 下载到 FireRedASR 项目目录下
    git clone https://huggingface.co/Qwen/Qwen2-7B-Instruct
    ```

4.  **创建软链接**：
    在 FireRedASR-LLM-L 的文件夹内，创建一个指向 Qwen2-7B-Instruct 的软链接，让模型能找到它。
    ```bash
    cd FireRedASR-LLM-L
    ln -s ../Qwen2-7B-Instruct ./
    cd ..
    ```
    

### 🚀 第三步：运行推理测试
环境配置好，模型下载完，就可以运行测试了。官方提供了一个方便的脚本 `speech2text.py`。

1.  **准备音频文件**：
    确保你的音频是 **16kHz 采样率、16-bit 位深的单声道 PCM WAV 格式**。如果你的音频格式不符，可以使用 `ffmpeg` 进行转换 ：
    ```bash
    # 安装ffmpeg (如果未安装)
    sudo apt-get install ffmpeg
    # 转换音频示例
    ffmpeg -i your_audio.mp3 -ar 16000 -ac 1 -sample_fmt s16 output.wav
    ```

2.  **执行识别**：
    使用 `--use_gpu 0` 指定使用第一块 GPU 进行推理。
    ```bash
    python speech2text.py \
        --wav_path /path/to/your/audio.wav \
        --asr_type "llm" \
        --model_dir ./FireRedASR-LLM-L \
        --use_gpu 0
    ```
    将 `/path/to/your/audio.wav` 替换为你实际的音频文件路径。
    

### 💡 针对"语音输入法"的特别优化建议
将模型部署为实时语音输入法，需要处理连续的音频流。以下是一些关键点：

*   **处理实时音频流**：你需要编写一个程序，从麦克风实时获取音频数据，将其按 **≤30秒** 的长度进行分段（因为该模型输入限制为30秒 ），然后依次调用 `speech2text.py` 或将其封装成一个函数进行循环调用。
*   **利用缓存机制**：在流式处理时，可以利用模型内部的 `cache` 机制来避免重复计算，从而提升效率。这需要参考官方提供的 API 进行更底层的代码实现 。
*   **音频格式**：务必保证送入模型的音频流是 **16kHz、单声道、16-bit PCM** 格式。

### ⚠️ 注意事项
*   **音频长度限制**：LLM 版本当前支持最长 **30秒** 的音频输入。对于超过30秒的语音，需要你主动进行切分 。
*   **硬件资源**：你的 RTX A6000 是官方推荐的理想配置，可以完美运行 。
*   **备选方案**：如果在测试中发现 LLM 版本的延迟无法满足你的实时性要求，可以随时回退到我们之前聊过的 **Paraformer-zh-streaming**，它在流畅度上做了极致优化，部署也同样简单 。

如果在部署过程中遇到任何具体的报错信息，随时可以再来问我。祝你部署顺利！
