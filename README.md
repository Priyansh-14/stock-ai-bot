# Stock AI Bot Backend

A custom backend using FastAPI that uses Perplexity AI to provide real-time research for stock tickers.

## Features

- Real-time Perplexity API queries
- FastAPI REST endpoint
- No frontend

## **How to Run This Backend**

### **1. Clone or Download the Code**

### **2. Create and Activate a Virtual Environment (optional but recommended)**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Set Up Environment Variables**

Create a `.env` file in your project directory with your Perplexity API key:

```
PERPLEXITY_API_KEY=your_actual_perplexity_api_key_here
```

### **5. Run the Backend Locally**

Use Uvicorn to start your FastAPI app (assuming your main file is `main.py` and your app instance is named `app`):

```bash
uvicorn main:app --reload --port 5000
```

- The `--reload` flag enables auto-reloading on code changes (for development)[2].
- The API will be available at `http://127.0.0.1:5000`.

### **6. Test the Endpoint**

Send a POST request to `/analyze` with a JSON body like:

```json
{
  "ticker": "MSFT"
}
```

You can use tools like [curl](https://curl.se/) or [Postman](https://www.postman.com/):

```bash
curl -X POST "http://127.0.0.1:5000/analyze" -H "Content-Type: application/json" -d '{"ticker": "MSFT"}'
```
