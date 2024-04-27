from langchain.pydantic_v1 import BaseModel
from tools.base_learningpath_tool import BaseLearningPathTool
from tools.learningpath_input import LaunchDarklyLearningPathInput
from typing import Type
from configs import Configs

class LaunchDarklyLearningPathTool(BaseLearningPathTool):
    service: str = "launchdarkly"
    name = Configs.get_service_config("launchdarkly", "tool.name", "learningpath")
    description = Configs.get_service_config("launchdarkly", "tool.description", "learningpath")
    args_schema: Type[BaseModel] = LaunchDarklyLearningPathInput
    
    
    