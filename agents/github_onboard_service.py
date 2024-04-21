from agents.onboard_service import OnboardService
from langchain.pydantic_v1 import BaseModel
from typing import Type
from agents.onboarding_input import GitHubInput

class GitHubOnboardService(OnboardService):
    serviceArgSchema: Type[BaseModel] = GitHubInput
    
    async def onboard(self, user_data):
        print(user_data)    