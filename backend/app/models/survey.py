from typing import Literal, Optional
from pydantic import BaseModel
from datetime import datetime

class SurveyResponse(BaseModel):
  question1: Literal[1, 2, 3, 4, 5]
  question2: Literal[1, 2, 3, 4, 5]
  question3: Literal[1, 2, 3, 4, 5]
  question4: Literal[1, 2, 3, 4, 5]
  question5: Literal[1, 2, 3, 4, 5]
  question6: Literal[1, 2, 3, 4, 5]
  question7: Literal[1, 2, 3, 4, 5]
  question8: Literal[1, 2, 3, 4, 5]
  question9: Literal[1, 2, 3, 4, 5]
  question10: Literal[1, 2, 3, 4, 5]
  question11: Literal[1, 2, 3, 4, 5]
  question12: Literal[1, 2, 3, 4, 5]
  question13: Literal[1, 2, 3, 4, 5]
  improvement_suggestion: Optional[str] = None

class Survey(BaseModel):
  user_id: str
  consent_hash: Optional[str] = None
  is_consented: bool = False

  survey_response: SurveyResponse
  survey_completed: bool = False
  expire_at: datetime