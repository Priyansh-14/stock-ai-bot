import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

if not PERPLEXITY_API_KEY:
    raise RuntimeError("PERPLEXITY_API_KEY not set in environment.")

app = FastAPI()

class StockQuery(BaseModel):
    ticker: str

def build_prompt(ticker: str) -> str:
    return (
        f"Give a detailed, real-time analysis of the stock '{ticker}'. "
        f"Include company performance, recent news, earnings, technical indicators, and analyst sentiment. "
        f"Use live web sources where necessary. Respond in a factual, professional tone."
    )

def get_stock_research(prompt: str):
    url = PERPLEXITY_API_URL
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3-sonar-small-32k-online",  # Can also try "sonar-medium"
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Perplexity API call failed")

    return response.json()["choices"][0]["message"]["content"]

@app.post("/analyze")
def analyze_stock(stockQuery: StockQuery):
    prompt = build_prompt(stockQuery.ticker.upper())
    try:
        result = get_stock_research(prompt)
        return {"ticker": stockQuery.ticker.upper(), "analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
