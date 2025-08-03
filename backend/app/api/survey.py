from typing import Dict, Optional
from fastapi import APIRouter, Body
from app.services.survey_service import SurveyService
from app.models.user_survey import UserSurvey
from app.db.mongodb import mongodb
from pydantic import BaseModel

class SurveyRes(BaseModel):
  user_id: str
  consent_hash: Optional[str] = None
  survey_res: Optional[Dict[str, object]] = None

router = APIRouter(prefix="/survey", tags=["survey"])

@router.post("/consent-status")
async def checkConsentStatus(data: SurveyRes = Body(...)):
  user_id = data.user_id
  return await SurveyService(UserSurvey(mongodb.db)).is_consented(user_id)

@router.post("/save-consent")
async def saveConsent(data: SurveyRes = Body(...)):
  user_id = data.user_id
  consent_hash = data.consent_hash
  await SurveyService(UserSurvey(mongodb.db)).save_consent(user_id, consent_hash)

@router.post("/save-survey")
async def saveSurvey(data: SurveyRes = Body(...)):
  user_id = data.user_id
  survey_res = data.survey_res
  await SurveyService(UserSurvey(mongodb.db)).save_survey_response(user_id, survey_res)