from langchain.pydantic_v1 import BaseModel
from tools.base_learningpath_tool import BaseLearningPathTool
from tools.learningpath_input import SnykLearningPathInput
from typing import Type
from configs import Configs

class SnykLearningPathTool(BaseLearningPathTool):
    service: str = "snyk"
    name = Configs.get_service_config("snyk", "tool.name", "learningpath")
    description = Configs.get_service_config("snyk", "tool.description", "learningpath")
    args_schema: Type[BaseModel] = SnykLearningPathInput