import os
import requests
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from random import random
from fastapi.security.api_key import APIKey
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security, HTTPException
from starlette.status import HTTP_403_FORBIDDEN

GPT_API_TOKEN = os.getenv("GPT_API_TOKEN")
API_KEY = os.getenv("API_KEY")

GPT_MODEL = os.getenv("GPT_MODEL", default="gpt-3.5-turbo")
GPT_PROMPT = os.getenv("GPT_PROMPT", default="Antworte kurz:")
# GPT_TEMPERATURE = float(os.getenv("GPT_TEMPERATURE", default="0.5"))
GPT_MAX_TOKENS = int(os.getenv("GPT_MAX_TOKENS", default="256"))

app = FastAPI()
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


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


async def verify_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API KEY"
        )


@app.post("/v1/completions")
async def completions(request_body: CompletionRequest, api_key: APIKey = Depends(verify_api_key)):
    request_body.model_dump_json()
    return query_gpt_completions_api(request_body.query)
