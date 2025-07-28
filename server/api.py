import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from shared.response_generator import ResponseGenerator

app = FastAPI(title="Support Agent API")

# Load once globally
print("Loading AI models...")
generator = ResponseGenerator()
print("Models loaded!")

class TicketRequest(BaseModel):
    text: str

@app.post("/generate")
async def generate_response(ticket: TicketRequest):
    try:
        result = generator.generate_response(ticket.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Support agent API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)