from fastapi import FastAPI
from src.scripts.check_env import main



# app = FastAPI()

# @app.get("/health")
# def health():
#     return {'status':'ok'}


main()