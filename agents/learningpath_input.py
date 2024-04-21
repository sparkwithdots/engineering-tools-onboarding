from langchain.pydantic_v1 import BaseModel, Field
from typing import List


class LaunchDarklyLearningPathInput(BaseModel):
    level: str = Field(description="LaunchDarkly knowledge level", title="LaunchDarkly Knowledge Level", default=None)
    preferences: List[str] = Field(description="Get the list of topics from available LaunchDarkly learning objects based preferences.", title="LaunchDarkly Learning Preferences", default=[])
    
class SnykLearningPathInput(BaseModel):
    level: str = Field(description="Snyk knowledge level", title="Snyk Knowledge Level", default=None)
    preferences: List[str] = Field(description="Get the list of topics from available Snyk learning objects based preferences.", title="Snyk Learning Preferences", default=[])

class GitHubLearningPathInput(BaseModel):
    level: str = Field(description="GitHub knowledge level", title="GitHub Knowledge Level", default=None)
    preferences: List[str] = Field(description="Get the list of topics from available GitHub learning objects based preferences.", title="GitHub Learning Preferences", default=[])
    