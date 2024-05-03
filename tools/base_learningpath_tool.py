from langchain.tools import BaseTool
from typing import Any, Optional, List
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from configs import Configs
from utils.agent_utils import unfold_learning_objects
from utils.learning_object_search import generate_learning_objects_dataframe, search_learning_objects

class BaseLearningPathTool(BaseTool):
    
    service: str = ""
    return_direct = False
    
    def retrieve_learningpath(self, level: str, preferences: List[str]) -> Any:
        if len(preferences) == 0 and (not level or level not in ["beginner", "intermediate", "advanced"]):
            return "Sorry, I can't find an appropriate learning path for you. Or you can just simply choose from beginner, intermediate, or advanced."
        learningObjects = Configs.get_service_config(self.service, "learningObjects", "learningpath")
        if len(preferences) > 0:
            df = generate_learning_objects_dataframe()
            topics_with_preference = search_learning_objects(self.service, preferences, df)
            learningObjects = list(filter(lambda x: x["topic"] in topics_with_preference, learningObjects))
            response_prefix = f"Based on your preferences, here are the recommended learning objects on service {self.service}: \n"
        else:
            learningObjects = list(filter(lambda x: x["level"] == level, learningObjects))
            response_prefix = f"Here are the recommended learning objects to enhance your skill level on service {self.service} based on your current knowledge level as \"{level}\": \n"
        return unfold_learning_objects(learningObjects, response_prefix)
        
    def _run(self, level: str = "beginner", preferences: List[str] = [], run_manager: Optional[CallbackManagerForToolRun] = None) -> Any:
        return self.retrieve_learningpath(level, preferences)    
    
    async def _arun(self, level: str = "beginner", preferences: List[str] = [], run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> Any:
        return self.retrieve_learningpath(level, preferences)