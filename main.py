import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

class Query(BaseModel):
    ticker: str

def build_prompt(ticker: str) -> str:
    return (
        f"Give a detailed, real-time analysis of the stock '{ticker}'. "
        f"Include company performance, recent news, earnings, technical indicators, and analyst sentiment. "
        f"Use live web sources where necessary. Respond in a factual, professional tone."
    )

def query_perplexity(prompt: str):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3-sonar-small-32k-online",  # Can also try "sonar-medium"
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Perplexity API call failed")

    return response.json()["choices"][0]["message"]["content"]

@app.post("/analyze")
def analyze_stock(query: Query):
    prompt = build_prompt(query.ticker.upper())
    try:
        result = query_perplexity(prompt)
        return {"ticker": query.ticker.upper(), "analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
