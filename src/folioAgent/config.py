"""模型、密钥、超时等配置"""
import os
from dotenv import load_dotenv

load_dotenv()

upload_url = [
    {
        "name": "langgraph-core-concepts",
        "url": "/Users/fang/learning/folio-agent/data/corpus/langgraph-core-concepts.docx",
        "data_id": "concepts"
    }
]

def require_env(name:str):
    """加载环境变量"""
    value = os.getenv(name,"").strip()
    if not value:
        raise ValueError(f'传入的变量名{name}有误')
    return value