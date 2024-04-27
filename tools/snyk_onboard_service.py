from tools.onboard_service import OnboardService
from langchain.pydantic_v1 import BaseModel
from typing import Type
from tools.onboarding_input import SnykInput

class SnykOnboardService(OnboardService):
    serviceArgSchema: Type[BaseModel] = SnykInput
    
    async def onboard(self, user_data):
        print(user_data)    