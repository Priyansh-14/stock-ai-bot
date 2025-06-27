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
    print(PERPLEXITY_API_KEY)
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
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
    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=20)
        print("Perplexity API status:", response.status_code)
        print("Perplexity API response:", response.text)
        response.raise_for_status()
        data = response.json()
    
        # Defensive: check structure
        if (
            "choices" in data and
            isinstance(data["choices"], list) and
            data["choices"] and
            "message" in data["choices"][0] and
            "content" in data["choices"][0]["message"]
        ):
            return data["choices"][0]["message"]["content"]
    
        else:
            raise HTTPException(status_code=502, detail="Malformed response from Perplexity API.")
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Perplexity API request timed out.")
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Perplexity API error: {str(e)}")

@app.post("/analyze")
def analyze_stock(stockQuery: StockQuery):
    prompt = build_prompt(stockQuery.ticker.upper())
    try:
        result = get_stock_research(prompt)
        return {"ticker": stockQuery.ticker.upper(), "analysis": result}
    except HTTPException as e:
        raise e  # Let FastAPI handle HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error.")