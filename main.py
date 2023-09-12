import os
import requests
import databases
import sqlalchemy

from fastapi import FastAPI, Depends
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKey
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from random import random
from starlette.status import HTTP_403_FORBIDDEN
from typing import List

GPT_API_TOKEN = os.getenv("GPT_API_TOKEN")
API_KEY = os.getenv("API_KEY")

GPT_MODEL = os.getenv("GPT_MODEL", default="gpt-3.5-turbo")
GPT_PROMPT = os.getenv("GPT_PROMPT", default="Antworte kurz:")
# GPT_TEMPERATURE = float(os.getenv("GPT_TEMPERATURE", default="0.5"))
GPT_MAX_TOKENS = int(os.getenv("GPT_MAX_TOKENS", default="256"))

DATABASE_URL = os.getenv("DATABASE_URL", default="sqlite:///./test.db")

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

interactions_table = sqlalchemy.Table(
    "interactions",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("query", sqlalchemy.String),
    sqlalchemy.Column("temperature", sqlalchemy.Float),
    sqlalchemy.Column("timestamp", sqlalchemy.Integer),
    sqlalchemy.Column("response", sqlalchemy.String),
    sqlalchemy.Column("prompt_tokens", sqlalchemy.Integer),
    sqlalchemy.Column("completion_tokens", sqlalchemy.Integer),
    sqlalchemy.Column("total_tokens", sqlalchemy.Integer),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

app = FastAPI()
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


class CompletionRequest(BaseModel):
    query: str


class Interaction(BaseModel):
    id: int
    query: str
    temperature: float
    timestamp: int
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


async def query_gpt_completions_api(gpt_query: str) -> str:
    temperature = random()  # GPT_TEMPERATURE
    response = requests.post(
        url="https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {GPT_API_TOKEN}"},
        json={
            "model": GPT_MODEL,
            "messages": [{"role": "user", "content": f"{GPT_PROMPT.strip()} {gpt_query}"}],
            "temperature": temperature,
            "max_tokens": GPT_MAX_TOKENS,
        }
    )
    data = response.json()
    try:
        query_response = data["choices"][0]["message"]["content"]
        sql_query = interactions_table.insert().values(
            query=gpt_query,
            temperature=temperature,
            timestamp=data["created"],
            response=query_response,
            prompt_tokens=data["usage"]["prompt_tokens"],
            completion_tokens=data["usage"]["completion_tokens"],
            total_tokens=data["usage"]["total_tokens"],
        )
        await database.execute(sql_query)
        return query_response
    except KeyError:
        return data


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


async def verify_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API KEY"
        )


@app.post("/v1/completions")
async def completions(request_body: CompletionRequest, api_key: APIKey = Depends(verify_api_key)):
    return await query_gpt_completions_api(request_body.query)


@app.get("/interactions", response_model=List[Interaction])
async def interactions():
    query = interactions_table.select()
    return await database.fetch_all(query)
