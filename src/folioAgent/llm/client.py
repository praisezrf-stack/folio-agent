from langchain.chat_models import init_chat_model
from ..config import require_env


def create_model():
    return init_chat_model(
        model=require_env("DEEPSEEK_MODEL"),
        base_url=require_env("BASE_URL"),
        model_provider="openai",
        api_key=require_env("DEEPSEEK_API_KEY"),
    )
    
