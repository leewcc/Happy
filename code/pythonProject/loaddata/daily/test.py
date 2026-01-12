import os
from huggingface_hub import snapshot_download

# 配置参数
REPO_ID = "BadToBest/EchoMimicV2"  # 仓库名
LOCAL_DIR = r"A:\indextts\echomimic_v2\pretrained_weights"  # 本地保存路径
MIRROR_ENDPOINT = "https://hf-mirror.com"  # 国内镜像

# 关键：设置镜像环境变量（适配旧版本）
os.environ["HUGGINGFACE_HUB_ENDPOINT"] = MIRROR_ENDPOINT

# 下载整个仓库（自动处理 LFS 大文件，断点续传）
snapshot_download(
    repo_id=REPO_ID,
    local_dir=LOCAL_DIR,
    local_dir_use_symlinks=False,
    resume_download=True,  # 断点续传
    ignore_patterns=None  # 下载所有文件（包括子目录）
)

print(f"\n✅ 所有文件已下载完成，保存到：{LOCAL_DIR}")