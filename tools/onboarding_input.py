from langchain.pydantic_v1 import BaseModel, Field, EmailStr

class LaunchDarklyInput(BaseModel):
    service: str = Field(description="The service you are onboarding to", title="Service", default="launchdarkly")
    name: str = Field(description="Your full name", title="Full Name", default=None)
    email: EmailStr = Field(description="Your email", title="Email", default=None)
    department: str = Field(description="Your department", title="Department", default=None)
    project: str = Field(description="Your project", title="Project", default=None)
    
class SnykInput(BaseModel):
    service: str = Field(description="The service you are onboarding to", title="Service", default="snyk")
    name: str = Field(description="Your full name", title="Full Name", default=None)
    email: EmailStr = Field(description="Your email", title="Email", default=None)
    repository: str = Field(description="Your repository", title="Repository", default=None)
    branch: str = Field(description="Your branch", title="Branch", default=None)
    
class GitHubInput(BaseModel):
    service: str = Field(description="The service you are onboarding to", title="Service", default="github")
    name: str = Field(description="Your full name", title="Full Name", default=None)
    email: EmailStr = Field(description="Your email", title="Email", default=None)
    organization: str = Field(description="Your organization", title="Organization", default=None)
    role: str = Field(description="Your role", title="Role", default=None)
    
