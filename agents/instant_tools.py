from langchain.tools import tool
from utils.agent_utils import unfold_learning_objects
from configs import Configs


@tool(return_direct=False)
def lookup_learningobjects(service: str) -> str:
    """Lookup all the available learning objects for the service provided"""
    learningObjects = Configs.get_service_config(service.lower(), "learningObjects", "learningpath")
    response_prefix = f"All learning objects on service {service}: "
    return unfold_learning_objects(learningObjects, response_prefix)
    
    