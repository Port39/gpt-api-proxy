import requests
import os
from fastapi import FastAPI
from pydantic import BaseModel
from random import random

GPT_API_TOKEN = os.getenv("GPT_API_TOKEN")
GPT_MODEL = os.getenv("GPT_MODEL", default="gpt-3.5-turbo")
GPT_PROMPT = os.getenv("GPT_PROMPT", default="Antworte kurz:")
# GPT_TEMPERATURE = float(os.getenv("GPT_TEMPERATURE", default="0.5"))
GPT_MAX_TOKENS = int(os.getenv("GPT_MAX_TOKENS", default="256"))

app = FastAPI()


class CompletionRequest(BaseModel):
    query: str


def query_gpt_completions_api(query: str) -> str:
    response = requests.post(
        url="https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {GPT_API_TOKEN}"},
        json={
            "model": GPT_MODEL,
            "messages": [{"role": "user", "content": f"{GPT_PROMPT.strip()} {query}"}],
            "temperature": random(),  # GPT_TEMPERATURE
            "max_tokens": GPT_MAX_TOKENS,
        }
    )
    try:
        return response.json()["choices"][0]["message"]["content"]
    except KeyError:
        return response.json()


@app.post("/v1/completions")
async def completions(request_body: CompletionRequest):
    request_body.model_dump_json()
    return query_gpt_completions_api(request_body.query)
