"""模型、密钥、超时等配置"""

import os, hashlib
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

upload_url = []


def get_doc():
    path = Path("/Users/fang/learning/folio-agent/data/corpus")
    for item in path.iterdir():
        upload_url.append(
            {
                "name": item.name,
                "url": str(item),
                "suffix": item.suffix,
                "data_id": hashlib.sha256(item.name.encode("utf-8")).hexdigest(),
            }
        )
    return upload_url


def require_env(name: str):
    """加载环境变量"""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"传入的变量名{name}有误")
    return value


if __name__ == "__main__":
    get_doc()
