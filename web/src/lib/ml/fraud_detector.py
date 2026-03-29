import pickle
import json
import numpy as np
import os
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Adjust paths to where Next.js is running from (web/)
model_path = os.path.join(os.path.dirname(__file__), 'model', 'model_b_xgboost.pkl')
meta_path = os.path.join(os.path.dirname(__file__), 'model', 'feature_metadata.json')

model = None
feature_metadata = None

if os.path.exists(model_path):
    print(f"Loading real model from {model_path}...")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print(f"Model successfully loaded. Type: {type(model)}")
    print(f"Expected n_features: {model.n_features_in_}")
else:
    print(f"Model not found at {model_path}")

if os.path.exists(meta_path):
    with open(meta_path, 'r') as f:
        feature_metadata = json.load(f)

app = FastAPI()

class Transaction(BaseModel):
    features: List[float]  # 22 features in exact order

class PredictionResponse(BaseModel):
    fraud_risk_score: float
    risk_bucket: str
    predicted_label: int
    confidence: float

def get_risk_bucket(score: float) -> str:
    if score >= 0.85:
        return "critical"
    elif score >= 0.60:
        return "high"
    elif score >= 0.30:
        return "medium"
    else:
        return "low"

@app.post("/predict", response_model=PredictionResponse)
async def predict_fraud(transaction: Transaction):
    if not model:
         return PredictionResponse(
             fraud_risk_score=0.15,
             risk_bucket="low",
             predicted_label=0,
             confidence=0.85
         )

    try:
        # Validate input
        if len(transaction.features) != 22:
            raise HTTPException(
                status_code=400,
                detail=f"Expected 22 features, got {len(transaction.features)}"
            )
        
        print("------------------------------------------")
        print("Input features:", transaction.features)
        
        # Run prediction
        features_array = np.array([transaction.features], dtype=np.float32)
        print("Input array shape:", features_array.shape)
        
        proba = model.predict_proba(features_array)
        print("Raw proba:", proba)
        
        fraud_score = float(proba[0][1])
        predicted_label = int(np.argmax(proba[0]))
        confidence = float(np.max(proba[0]))
        
        print(f"Mapped output -> Score: {fraud_score:.4f}, Label: {predicted_label}, Conf: {confidence:.4f}")
        print("------------------------------------------")

        return PredictionResponse(
            fraud_risk_score=fraud_score,
            risk_bucket=get_risk_bucket(fraud_score),
            predicted_label=predicted_label,
            confidence=confidence
        )
    
    except Exception as e:
        print("Prediction error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
