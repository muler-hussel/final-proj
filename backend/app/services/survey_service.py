from typing import Dict
from app.models.user_survey import UserSurvey
from app.models.survey import SurveyResponse

class SurveyService:
  def __init__(self, user_survey: UserSurvey):
    self.user_survey = user_survey

  async def is_consented(self, user_id: str):
    return await self.user_survey.is_consented(user_id)
  
  async def save_consent(self, user_id: str, consent_hash: str):
    if not consent_hash:
      print("No hash consent available.")
    await self.user_survey.save_consent(user_id, consent_hash)
  
  async def save_survey_response(self, user_id: str, survey_res: Dict[str, object]):
    try:
      response = SurveyResponse(**survey_res)
      await self.user_survey.save_survey_response(user_id, response)
    except Exception as e:
      print(e)