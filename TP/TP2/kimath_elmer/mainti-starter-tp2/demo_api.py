from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class Reading (BaseModel):
    temperature_c: float = Field(e=40, le=150)
    vibration: float = Field(e=0, le=10)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/v1/predict")
def predict(reading: Reading):
    # Placeholder for prediction logic
    return {"alert": "reading.temperature_c > 80"}  