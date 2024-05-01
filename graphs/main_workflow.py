from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import Field
from typing import Annotated, Sequence, TypedDict
from functools import partial
from langgraph.prebuilt import ToolExecutor
from langgraph.graph import StateGraph, END
import uuid
import operator
from langchain_core.utils.function_calling import convert_to_openai_function
from utils.onboarding_utils import has_all_info, get_user_data, get_service_and_feature, get_service_and_feature_from_messages, collect_info_tool, confirm_information, call_model, call_tool, onboard_service, onboard_abort
import json
from utils.agent_utils import create_func_agent
from tools.onboard_service import OnboardService
from langgraph.checkpoint.base import BaseCheckpointSaver
from typing import List


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    service: Annotated[str, Field(description="The service the user is on", title="Service", default="")]
    feature: Annotated[str, Field(description="The feature the user is on", title="Feature", default="")]
    thread_id: Annotated[str, Field(description="The thread id for the conversation", title="Thread ID", default="")]

def get_general_messages(messages):
    sys_msg = """
    Your job is to help identify what service and feature the user is looking at. Currently the supported services are:
    - github
    - launchdarkly
    - snyk
    
    For each service, the supported features are:
    - onboarding: Help the user onboard to the service.
    - learningpath: Provide advice on the learning path for the service depends on user's knowledge level or preferences. User can request to learn or know something about the service.
    - query: Answer user's questions about the service other than onboarding and learning paths.
    
    For others, show user what you services and features you offer and ask them to provide what they need to request.
    """ 
    return [SystemMessage(content=sys_msg)] + messages

# Handle agent and convert to agent graph node
def agent_node(state, agent, name):
    messages = state["messages"]
    thread_id = state["thread_id"]
    service, feature = get_service_and_feature_from_messages(messages)
    
    if feature == "query":
        msg = None
        # Get the last human message
        for message in messages[::-1]:
            if isinstance(message, HumanMessage):
                msg = message
                break
        response = agent.invoke({"messages": [msg], "service": service, "feature": feature, "thread_id": thread_id})
    else:
        response = agent.invoke(state)
    content = response["output"]
    cur_service, cur_feature = state["service"], state["feature"]
    if service and service != "" and feature and feature != "" and cur_service and cur_service != "" and cur_feature and cur_feature != "":
        if cur_service != service or cur_feature != feature:
            thread_id = str(uuid.uuid4())
    return {"messages": [HumanMessage(content=content, name=name)], "service": service, "feature": feature, "thread_id": thread_id}

# route function for conditional edges
def route(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then finish
    if "function_call" not in last_message.additional_kwargs:
        return "End"
    else:
        if last_message.additional_kwargs["function_call"]["name"] == "get_service_and_feature":
            choices = json.loads(last_message.additional_kwargs["function_call"]["arguments"])
            if "service" in choices.keys() and "feature" in choices.keys():
                service, feature = choices["service"], choices["feature"]
                if service == "" or feature == "":
                    return "general"
                else:
                    if feature == "onboarding":
                        return f"{service}_CollectInfoAgent"
                    else:              
                        return f"{service}_{feature}"
            else:
                return "general"
        else:
            service, _ = get_service_and_feature_from_messages(messages)
            if not service or service == "":
                raise ValueError("Service is not provided.")
            if last_message.additional_kwargs["function_call"]["name"] in ["collect_info", "initiate_onboarding"]:
                user_data = get_user_data(messages)
                if has_all_info(service, user_data) == "":
                    return f"{service}_ConfirmInfoAgent"
                else:
                    return f"{service}_CollectInfoAction"
            elif last_message.additional_kwargs["function_call"]["name"] == "confirm_onboarding":
                data = json.loads(last_message.additional_kwargs["function_call"]["arguments"])
                if "choice" in data.keys():
                    if data["choice"] == "yes":
                        return f"{service}_OnboardAgent"
                    elif data["choice"] == "no":
                        return f"{service}_OnboardAbort"
                    else:
                        return f"{service}_ConfirmInfoAgent"
                else:
                    return "End"
            else:
                return "End"

class MainWorkflow():
    
    def __init__(self, llm: ChatOpenAI, memory: BaseCheckpointSaver = None):
        self.workflow = StateGraph(AgentState)
        self.llm = llm
        self.memory = memory
        self.onboarding_nodes = {}
        self.learningpath_nodes = {}
        self.onboarding_services = []
        self.learningpath_services = []
        self.query_nodes = {}
        self.query_services = []
        self.graph = None
    
    def register_onboarding_service(self, service: str, onboard_svc: OnboardService, llm:ChatOpenAI):
        
        collect_info_func = collect_info_tool(onboardService=onboard_svc)       
        tool_executor = ToolExecutor([collect_info_func])
        model = llm.bind_functions(functions=[convert_to_openai_function(t) for t in [collect_info_func]], function_call="auto")
        collect_info_agent = partial(call_model, model=model, base_model=llm)
        collect_info_action = partial(call_tool, tool_executor=tool_executor)
        onboard_svc_func = partial(onboard_service, onboardService=onboard_svc)
        
        self.onboarding_nodes[f"{service}_CollectInfoAgent"] = collect_info_agent
        self.onboarding_nodes[f"{service}_CollectInfoAction"] = collect_info_action
        self.onboarding_nodes[f"{service}_ConfirmInfoAgent"] = confirm_information
        self.onboarding_nodes[f"{service}_OnboardAgent"] = onboard_svc_func
        self.onboarding_nodes[f"{service}_OnboardAbort"] = onboard_abort
        
        self.onboarding_services.append(service)
    
    def register_learningpath_service(self, service: str, prompt_path: str, prompt_data: dict, tools: List, llm: ChatOpenAI):
        name, learningpath_agent = create_func_agent(name=f"{service}_learningpath", sys_prompt_path=prompt_path, sys_prompt_data=prompt_data, tools=tools, llm=llm)
        learningpath_node = partial(agent_node, agent=learningpath_agent, name=name)
        self.learningpath_nodes[name] = learningpath_node
        self.learningpath_services.append(service)
        
    def register_query_service(self, service: str, prompt_path: str, prompt_data: dict, tools: List, llm: ChatOpenAI):
        name, query_agent = create_func_agent(name=f"{service}_query", sys_prompt_path=prompt_path, sys_prompt_data=prompt_data, tools=tools, llm=llm)
        query_node = partial(agent_node, agent=query_agent, name=name)
        self.query_nodes[name] = query_node
        self.query_services.append(service)
        
    def build_graph(self):
        router_model = self.llm.bind_functions(functions=[convert_to_openai_function(t) for t in [get_service_and_feature]], function_call="get_service_and_feature")
        router_chain = get_general_messages | router_model
        router = partial(call_model, model=router_chain, base_model=self.llm)

        general_chain = get_general_messages | self.llm
        general_node = partial(call_model, model=general_chain, base_model=self.llm)
        
        self.workflow.add_node("router", router)
        nodes = {}
        
        if len(self.onboarding_nodes) == 0 or len(self.learningpath_nodes) == 0 or len(self.query_nodes) == 0:
            raise ValueError("No nodes have been registered")
        for name, node in self.onboarding_nodes.items():
            self.workflow.add_node(name, node)
            nodes[name] = name
        for name, node in self.learningpath_nodes.items():
            self.workflow.add_node(name, node)
            nodes[name] = name
        for name, node in self.query_nodes.items():
            self.workflow.add_node(name, node)
            nodes[name] = name
        self.workflow.add_node("general", general_node)
        nodes["general"] = "general"
        nodes["End"] = END
        self.workflow.add_conditional_edges("router", route, nodes)
        for service in self.onboarding_services:
            self.workflow.add_conditional_edges(f"{service}_CollectInfoAgent", route, {
                f"{service}_CollectInfoAction": f"{service}_CollectInfoAction",
                f"{service}_ConfirmInfoAgent": f"{service}_ConfirmInfoAgent",
                f"{service}_OnboardAgent": f"{service}_OnboardAgent",
                f"{service}_OnboardAbort": f"{service}_OnboardAbort",
                "End": END
            })
            self.workflow.add_conditional_edges(f"{service}_ConfirmInfoAgent", route, {
                f"{service}_ConfirmInfoAgent": f"{service}_ConfirmInfoAgent",
                f"{service}_OnboardAgent": f"{service}_OnboardAgent",
                f"{service}_OnboardAbort": f"{service}_OnboardAbort",
                "End": END
            })
            self.workflow.add_edge(f"{service}_CollectInfoAction", f"{service}_CollectInfoAgent")
            self.workflow.add_edge(f"{service}_OnboardAgent", END)
            self.workflow.add_edge(f"{service}_OnboardAbort", END)
    
        for service in self.learningpath_services:
            self.workflow.add_edge(f"{service}_learningpath", END)
        
        for service in self.query_services:
            self.workflow.add_edge(f"{service}_query", END)
        
        self.workflow.add_edge("general", END)
        self.workflow.set_entry_point("router")
        self.graph = self.workflow.compile(checkpointer=self.memory)
        return self.graph

    def update_state_after_onboarding(self, config: RunnableConfig):
        cur_state = self.graph.get_state(config=config).values
        if cur_state:
            messages = cur_state["messages"]
            if isinstance(messages[-1], AIMessage) and "onboard_status" in messages[-1].additional_kwargs and messages[-1].additional_kwargs["onboard_status"] == "completed":
                print("Onboarding completed, updating thread id")
                thread_id = str(uuid.uuid4())
                config["configurable"]["thread_id"] = thread_id
    
    def update_state(self, config: RunnableConfig, prev_msgs: List[BaseMessage]):
        cur_state = self.graph.get_state(config=config).values
        prev_msgs.clear()
        if cur_state:
            messages = cur_state["messages"]            
            cur_thread_id = cur_state["thread_id"]
            if cur_thread_id and cur_thread_id != "":
                if config["configurable"]["thread_id"] != cur_thread_id:
                    for message in messages[::-1]:
                        if isinstance(message, HumanMessage):
                            prev_msgs.append(message)
                            break
                    config["configurable"]["thread_id"] = cur_thread_id
        
