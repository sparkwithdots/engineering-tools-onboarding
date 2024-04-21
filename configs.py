import yaml
from typing import Any

class Configs:
    
    @staticmethod
    def get_value(data: dict, path: str) -> Any:
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    @staticmethod
    def get_configs(name: str) -> dict:
        with open(f"configs/{name}.yaml", "r") as file:
            return yaml.safe_load(file)
        
    @staticmethod
    def onboarding_configs() -> dict:
        return Configs.get_configs("onboarding")
    
    @staticmethod
    def learningpath_configs() -> dict:
        return Configs.get_configs("learningpath")
    
    @staticmethod
    def rag_configs() -> dict:
        return Configs.get_configs("rag")
    
    @staticmethod
    def get_service_config(service: str, key: str, config: str = "onboarding") -> Any:
        data = Configs.get_value(Configs.get_configs(config), "services." + service)
        return Configs.get_value(data, key)
