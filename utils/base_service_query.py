from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import BasePromptTemplate
from rag.service_retriever import ServiceRetriever

class BaseServiceQuery():
    
    def __init__(self, service: str, document_prompt: BasePromptTemplate=None):
        self.service = service
        self.service_retriever = ServiceRetriever(service=service)
        self.document_prompt = document_prompt
        
    
    def build_retriever_tool(self, name: str, description: str):
        retriever = self.service_retriever.get_retriever()
        tool = create_retriever_tool(
            name=name,
            description=description,
            retriever=retriever,
            document_prompt=self.document_prompt
        )
        return tool
        