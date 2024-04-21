from langchain_core.pydantic_v1 import BaseModel
from typing import Type


class OnboardService():
    
    serviceArgSchema: Type[BaseModel] = None
    
    def __init__(self, service: str):
        self.service = service
        
    async def onboard(self, user_data):
        raise NotImplementedError("onboard method must be implemented in the subclass")
