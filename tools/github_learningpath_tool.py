from langchain.pydantic_v1 import BaseModel
from tools.base_learningpath_tool import BaseLearningPathTool
from tools.learningpath_input import GitHubLearningPathInput
from typing import Type
from configs import Configs

class GitHubLearningPathTool(BaseLearningPathTool):
    service: str = "github"
    name = Configs.get_service_config("github", "tool.name", "learningpath")
    description = Configs.get_service_config("github", "tool.description", "learningpath")
    args_schema: Type[BaseModel] = GitHubLearningPathInput