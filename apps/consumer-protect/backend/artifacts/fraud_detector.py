from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover
    ort = None


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger("satark-fraud-detector")

app = FastAPI(title="SATARK Fraud Detector", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR  # model files sit alongside this script
PKL_PATH = MODEL_DIR / "model_b_xgboost.pkl"
ONNX_PATH = MODEL_DIR / "model_b_xgboost.onnx"
FEATURE_META_PATH = MODEL_DIR / "feature_metadata.json"

# Loaded once at startup
model: Any = None
onnx_session: Optional["ort.InferenceSession"] = None
feature_meta: Dict[str, Any] = {}


class PredictRequest(BaseModel):
    # Preferred: send named features so the service can build the vector safely.
    # If you already have a list from the frontend, send it in `features`.
    features: Optional[List[float]] = Field(default=None)
    amount: Optional[float] = None
    senderVpa: Optional[str] = None
    recipientVpa: Optional[str] = None
    remark: Optional[str] = None
    recipientAgeDays: Optional[int] = None
    recipientFanIn7d: Optional[int] = None
    isNewDevice: Optional[bool] = None
    ipStateMatch: Optional[bool] = None
    sessionDurationSec: Optional[float] = None
    isVpn: Optional[bool] = None


def _load_feature_meta() -> Dict[str, Any]:
    if FEATURE_META_PATH.exists():
        with open(FEATURE_META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
            logger.info("Loaded feature metadata: %s", FEATURE_META_PATH)
            return meta
    logger.warning("feature_metadata.json not found at %s", FEATURE_META_PATH)
    return {}


def _load_model() -> Any:
    global onnx_session

    if PKL_PATH.exists():
        if joblib is None:
            raise RuntimeError("joblib is required to load the .pkl model but is not installed.")
        logger.info("Loading PKL model from %s", PKL_PATH)
        loaded = joblib.load(PKL_PATH)
        logger.info("Loaded model type: %s", type(loaded))
        return loaded

    if ONNX_PATH.exists():
        if ort is None:
            raise RuntimeError("onnxruntime is required to load the .onnx model but is not installed.")
        logger.info("Loading ONNX model from %s", ONNX_PATH)
        onnx_session = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])
        logger.info("ONNX input names: %s", [i.name for i in onnx_session.get_inputs()])
        logger.info("ONNX output names: %s", [o.name for o in onnx_session.get_outputs()])
        return onnx_session

    raise FileNotFoundError(
        f"Neither {PKL_PATH.name} nor {ONNX_PATH.name} was found in {MODEL_DIR}"
    )


def _build_feature_vector(req: PredictRequest) -> np.ndarray:
    """
    Build the exact 22-feature vector expected by the backend pipeline.
    If the frontend already sends `features`, use that directly.
    Otherwise construct a safe default vector from the request fields.
    """
    if req.features is not None:
        vec = np.asarray(req.features, dtype=np.float32)
        return vec

    # Safe defaults for manual testing.
    # IMPORTANT: keep this aligned with the training feature order.
    amount = float(req.amount or 0.0)
    recipient_age = int(req.recipientAgeDays or 365)
    fan_in = int(req.recipientFanIn7d or 1)
    new_device = 1.0 if req.isNewDevice else 0.0
    ip_match = 1.0 if (req.ipStateMatch is None or req.ipStateMatch) else 0.0
    vpn = 1.0 if req.isVpn else 0.0
    session_sec = float(req.sessionDurationSec or 120.0)

    # You should replace these defaults with the exact feature builder logic
    # used by your frontend if you are sending named UI inputs directly.
    vec = np.array(
        [
            min(amount / 100000.0, 1.0),   # example normalized amount
            4.0,                           # placeholder structural feature
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            float(fan_in),
            float(recipient_age),
            np.log1p(amount) / np.log1p(100000.0) if amount > 0 else 0.0,
            new_device,
            ip_match,
            vpn,
            session_sec / 600.0,
            0.0,
            float(recipient_age),
            float(fan_in),
            1.0,
            amount,
            1.0 if amount >= 50000 else 0.0,
            amount,
            0.0,
        ],
        dtype=np.float32,
    )
    return vec


def _predict_with_pkl(model_obj: Any, feature_vector: np.ndarray) -> Dict[str, Any]:
    x = feature_vector.reshape(1, -1)
    logger.info("Predicting with PKL model. Input shape=%s", x.shape)

    if hasattr(model_obj, "predict_proba"):
        proba = model_obj.predict_proba(x)
        score = float(proba[0][1]) if proba.shape[1] > 1 else float(proba[0][0])
        pred = int(score >= 0.5)
    elif hasattr(model_obj, "predict"):
        pred_val = model_obj.predict(x)
        pred = int(pred_val[0])
        score = float(pred)
    else:
        raise RuntimeError("Loaded PKL model does not support predict_proba or predict")

    risk_bucket = "low"
    if score >= 0.75:
        risk_bucket = "critical"
    elif score >= 0.55:
        risk_bucket = "high"
    elif score >= 0.30:
        risk_bucket = "medium"

    return {
        "fraud_risk_score": score,
        "risk_bucket": risk_bucket,
        "predicted_label": pred,
        "confidence": score,
    }


def _predict_with_onnx(session: "ort.InferenceSession", feature_vector: np.ndarray) -> Dict[str, Any]:
    x = feature_vector.astype(np.float32).reshape(1, -1)

    input_name = session.get_inputs()[0].name
    output_names = [o.name for o in session.get_outputs()]
    logger.info("Predicting with ONNX. input=%s outputs=%s", input_name, output_names)

    outputs = session.run(None, {input_name: x})

    # Try to find class probabilities in a robust way
    score = None
    pred = None

    for out in outputs:
        arr = np.asarray(out)
        if arr.ndim == 2 and arr.shape[1] >= 2:
            score = float(arr[0][1])
            pred = int(score >= 0.5)
            break

    if score is None:
        # fallback if model outputs a single score
        arr = np.asarray(outputs[0]).reshape(-1)
        score = float(arr[0])
        pred = int(score >= 0.5)

    risk_bucket = "low"
    if score >= 0.75:
        risk_bucket = "critical"
    elif score >= 0.55:
        risk_bucket = "high"
    elif score >= 0.30:
        risk_bucket = "medium"

    return {
        "fraud_risk_score": score,
        "risk_bucket": risk_bucket,
        "predicted_label": pred,
        "confidence": score,
    }


@app.on_event("startup")
def startup_event() -> None:
    global model, feature_meta
    feature_meta = _load_feature_meta()
    model = _load_model()
    logger.info("SATARK fraud detector ready.")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest) -> Dict[str, Any]:
    try:
        fv = _build_feature_vector(req)
        logger.info("[TRACE] feature_vector=%s", fv.tolist())

        # If frontend sends a fixed number of features, log it
        if feature_meta.get("n_features") and len(fv) != int(feature_meta["n_features"]):
            logger.warning(
                "Feature length mismatch: got %d expected %s",
                len(fv),
                feature_meta.get("n_features"),
            )

        if isinstance(model, np.ndarray):
            raise RuntimeError("Model is invalid.")

        if onnx_session is not None:
            result = _predict_with_onnx(onnx_session, fv)
        else:
            result = _predict_with_pkl(model, fv)

        logger.info("[TRACE] prediction=%s", result)
        return result

    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fraud_detector:app", host="0.0.0.0", port=8000, reload=True)