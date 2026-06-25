from fastapi import APIRouter, Depends
from app.ml.risk_model import risk_scorer
from app.schemas.chat import RiskRequest
from app.security.dependencies import get_current_user

router = APIRouter()

@router.post("/risk-score")
async def risk_score(payload: RiskRequest, _=Depends(get_current_user)):
    return risk_scorer.predict(payload.text)

@router.get("/model")
async def model_info(_=Depends(get_current_user)):
    return {"model_version": risk_scorer.version, "model_path": str(risk_scorer.model_path), "labels": risk_scorer.model.get("labels", [])}
