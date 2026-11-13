from langchain.chat_models import init_chat_model
from ..config import require_env

from langchain_huggingface import HuggingFaceEmbeddings

def create_model():
    return init_chat_model(
        model=require_env("MODEL"),
        base_url=require_env("BASE_URL"),
        model_provider="openai",
        api_key=require_env("API_KEY"),
    )


def get_embedder():
    return HuggingFaceEmbeddings(
        model_name=require_env('EMBED_MODEL'),
        model_kwargs={
            'device':"cpu"
        }
    )

