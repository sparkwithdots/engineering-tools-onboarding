from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from typing import Any, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate


def unfold_learning_objects(learningObjects: List, response_prefix: str) -> Any:
    response = response_prefix
    for obj in learningObjects:
        response += f"  \nTopic: {obj['topic']}  \nDescription: {obj['description']}  \nLevel: {obj['level']}  \n"
    return response

def create_func_agent(name: str, sys_prompt_path: str, sys_prompt_data: dict, tools: List, llm: ChatOpenAI):
    sys_template = PromptTemplate.from_file(sys_prompt_path)
    sys_prompt = sys_template.format(**sys_prompt_data)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", sys_prompt),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    func_agent = create_openai_functions_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=func_agent, tools=tools, verbose=True)
    return name, executor

