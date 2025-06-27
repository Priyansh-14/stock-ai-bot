import os
import re
from fastapi.responses import FileResponse
import requests
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
from io import BytesIO

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar"

# sonar-deep-research
# sonar-reasoning-pro
# sonar-reasoning
# sonar-pro sonar
# sonar

if not PERPLEXITY_API_KEY:
    raise RuntimeError("PERPLEXITY_API_KEY not set in environment.")

app = FastAPI()
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
# Serve static files (including index.html) from a 'static' folder
app.mount("/static", StaticFiles(directory="static"), name="static")



class StockQuery(BaseModel):
    ticker: str

def build_prompt(ticker: str) -> str:
    return (
        f"Give a detailed, real-time analysis of the stock '{ticker}'. "
        f"Include company performance, recent news, earnings, technical indicators, analyst sentiment, and relevant charts or images. "
        f"Use live web sources where necessary. Respond in a factual, professional tone. "
        f"include links to images or charts."
    )

def get_stock_research(prompt: str):
    # print(PERPLEXITY_API_KEY)
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload)
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
            # print(data)
            return data
            # return data["choices"][0]["message"]["content"]
    
        else:
            raise HTTPException(status_code=502, detail="Malformed response from Perplexity API.")
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Perplexity API request timed out.")
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Perplexity API error: {str(e)}")

def extract_image_urls(text):
    # Simple regex for image URLs (jpg, png, gif, svg, webp)
    return re.findall(r'(https?://\S+\.(?:png|jpg|jpeg|gif|svg|webp))', text)

def export_to_pdf(ticker: str, analysis: str, citations: list) -> str:
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{ticker}_{timestamp}.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Stock Analysis Report: {ticker}")
    y -= 30

    # Extract image URLs
    image_urls = extract_image_urls(analysis)
    for url in image_urls:
        analysis = analysis.replace(url, '')

    # Add analysis text
    c.setFont("Helvetica", 12)
    textobject = c.beginText(50, y)
    for line in analysis.splitlines():
        if y < 100:
            c.drawText(textobject)
            c.showPage()
            y = height - 50
            textobject = c.beginText(50, y)
        textobject.textLine(line)
        y -= 15
    c.drawText(textobject)
    y -= 10

    # Add images
    for url in image_urls:
        try:
            img_response = requests.get(url, timeout=10)
            img_response.raise_for_status()
            img = ImageReader(BytesIO(img_response.content))
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            display_width = min(400, width - 100)
            display_height = display_width * aspect
            if y - display_height < 50:
                c.showPage()
                y = height - 50
            c.drawImage(img, 50, y - display_height, width=display_width, height=display_height)
            y -= (display_height + 20)
        except Exception as e:
            print(f"Failed to add image {url}: {e}")
            continue

    # Add citations at the end
    if y < 150:
        c.showPage()
        y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Citations")
    y -= 25
    c.setFont("Helvetica", 10)
    for idx, cite in enumerate(citations, 1):
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.drawString(50, y, f"[{idx}] {cite}")
        y -= 15

    c.save()
    return filename

@app.post("/analyze")
def analyze_stock(stockQuery: StockQuery):
    prompt = build_prompt(stockQuery.ticker.upper())
    try:
        data = get_stock_research(prompt)
        result = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])
        pdf_path = export_to_pdf(stockQuery.ticker.upper(), result, citations)
        return {
            "ticker": stockQuery.ticker.upper(),
            "pdf_path": pdf_path
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error.")
    
@app.get("/")
def root():
    return FileResponse("static/index.html")