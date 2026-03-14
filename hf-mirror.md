`git clone` Hugging Face 慢是很多国内开发者的痛点。最直接有效的方法就是使用国内镜像站，通过简单的配置，就能将下载速度提升数倍甚至数十倍。

我整理了目前最主流、稳定的解决方案，你可以根据自己使用的工具，选择最适合的一种。

### ⚡️ 首选方案：配置 `hf-mirror.com` 镜像

`hf-mirror.com` 是目前国内最稳定、兼容性最好的 Hugging Face 镜像站，几乎支持所有的官方工具链 。你只需设置一个环境变量，所有下载请求都会自动指向这个加速镜像。

#### **针对你的 `git clone` 场景** 

如果你习惯使用 `git clone`，可以通过以下配置，让 Git 自动将请求重定向到镜像站，无需修改克隆地址：

```bash
# 配置 Git 使用镜像
git config --global url."https://hf-mirror.com/".insteadOf "https://huggingface.co/"

# 之后，直接克隆官方地址即可（实际会走镜像）
git clone https://huggingface.co/Qwen/Qwen2.5-3B-Instruct

# 进入目录后，记得拉取 LFS 大文件
cd Qwen2.5-3B-Instruct
git lfs pull
```

#### **环境变量配置（最通用）** 

这个环境变量对所有基于 `huggingface_hub` 的工具（如 `transformers`、`datasets`）都有效，强烈建议配置。

*   **临时生效**（仅当前终端）：
    ```bash
    # Linux / macOS
    export HF_ENDPOINT=https://hf-mirror.com

    # Windows PowerShell
    $env:HF_ENDPOINT = "https://hf-mirror.com"
    ```

*   **永久生效**（推荐）：
    *   **Linux / macOS**：将 `export HF_ENDPOINT=https://hf-mirror.com` 添加到 `~/.bashrc` 或 `~/.zshrc` 文件中，然后执行 `source ~/.bashrc`。
    *   **Windows**：在系统环境变量中新建一个变量，变量名为 `HF_ENDPOINT`，变量值为 `https://hf-mirror.com` 。

### 🚀 其他常用工具的加速方法

除了 `git clone`，你可能还会用到其他方式来获取模型，这里也一并为你列出加速方法。

*   **使用 `huggingface-cli` 命令行工具** 
    这是官方命令行工具，功能强大，支持断点续传。
    1.  **安装/升级**：`pip install -U huggingface_hub`
    2.  **配置环境变量**：参考上文设置 `HF_ENDPOINT`。
    3.  **下载模型**（以 `gpt2` 为例）：
        ```bash
        huggingface-cli download --resume-download gpt2 --local-dir ./gpt2 --local-dir-use-symlinks False
        ```
        *   `--resume-download`：支持断点续传，网络中断后可以继续下载 。
        *   `--local-dir-use-symlinks False`：确保下载到本地的是实体文件，而非符号链接，方便直接使用 。

*   **在 Python 代码中加速** 
    如果你在代码中直接使用 `from_pretrained` 加载模型，可以这样配置：
    ```python
    import os
    from transformers import AutoModel

    # 方法1：设置环境变量（在代码开头执行）
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

    # 之后正常加载模型即可
    model = AutoModel.from_pretrained("bert-base-chinese")
    ```

*   **使用镜像站专属加速脚本 `hfd`** 
    这是 `hf-mirror.com` 提供的基于 `aria2` 的下载脚本，多线程并发，速度非常暴力。
    1.  **安装 aria2**：`apt update && apt install aria2` (Linux)
    2.  **下载脚本**：
        ```bash
        wget https://hf-mirror.com/hfd/hfd.sh
        chmod a+x hfd.sh
        ```
    3.  **设置环境变量**：`export HF_ENDPOINT=https://hf-mirror.com`
    4.  **下载模型**：`./hfd.sh gpt2`
