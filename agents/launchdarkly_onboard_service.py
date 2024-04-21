from agents.onboard_service import OnboardService
from langchain.pydantic_v1 import BaseModel
from typing import Type
from agents.onboarding_input import LaunchDarklyInput

class LaunchDarklyOnboardService(OnboardService):
    serviceArgSchema: Type[BaseModel] = LaunchDarklyInput
    
    async def onboard(self, user_data):
        # Implement the actual onboarding logic here, by calling LaunchDarkly APIs
        print(user_data)    