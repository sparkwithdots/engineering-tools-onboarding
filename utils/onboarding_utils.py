from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, FunctionMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool, StructuredTool
from langgraph.prebuilt import ToolInvocation
import json
from langchain_core.utils.function_calling import convert_to_openai_function
import asyncio
from configs import Configs
import uuid


class ServiceAndFeatureInput(BaseModel):
    service: str = Field(description="The service the user is looking at, should be one of: github, launchdarkly, snyk", title="Service", default="")
    feature: str = Field(description="The supported features, should be one of: onboarding, learningpath, query", title="Feature", default="")

class ConfirmOnboardInput(BaseModel):
    choice: str = Field(description="Continue onboard or abort, should be one of: yes, no", title="Confirm", default=None)


@tool(return_direct=False, args_schema=ServiceAndFeatureInput)
def get_service_and_feature(state):
    """Identify the service and feature the user is looking at."""
    messages = state["messages"]
    return {
        "messages": [
            AIMessage(
                content=messages[-1].content,
                additional_kwargs={},
            )
        ]
    }

def get_service_and_feature_from_messages(messages):
    for message in messages[::-1]:
        if "function_call" in message.additional_kwargs and message.additional_kwargs["function_call"]["name"] == "get_service_and_feature":
            data = json.loads(message.additional_kwargs["function_call"]["arguments"])
            if "service" in data.keys() and "feature" in data.keys():
                return (data["service"], data["feature"])
    return ("", "")

def get_required_fields(service):
    service_config = Configs.get_value(Configs.onboarding_configs(), f"services.{service}")
    required_keys = service_config.get("required_keys", [])
    return [item["key"] for item in required_keys]

def has_all_info(service, user_data):
    fields = get_required_fields(service)
    if not user_data or len(user_data) == 0:
        return fields[0]
    for field in fields:
        if field not in user_data.keys() or not user_data[field] or user_data[field] == "" or user_data[field].lower() in ["n/a"]:
            return field
    return ""


@tool(return_direct=False, args_schema=ConfirmOnboardInput)
def confirm_onboarding(state):
    """Confirm the onboarding process"""
    messages = state["messages"]
    data = get_user_data(messages)
    if not data or len(data) == 0:
        msg = "No user data provided."
    else:
        msg = f"User data provided:\n" + " \n".join([f"{key}: {value}" for key, value in data.items()])
    return {
        "messages": [
            AIMessage(
                content=msg,
                additional_kwargs={},
            )
        ]
    }

def collect_info(**kwargs):
    """Collects the information from the user"""
    if not kwargs or len(kwargs) == 0 or "service" not in kwargs.keys():
        msg = "Required information is not provided yet"
        kwargs = {}
    else:
        service = kwargs["service"]
        user_data = kwargs.copy()
        del user_data["service"]
        if not user_data or len(user_data) == 0:
            msg = "No user data provided."
        else:
            missing_field = has_all_info(service, user_data)
            if missing_field == "":
                msg = "All information has been collected."
            else:
                msg = f"Still need to collect information for {missing_field}."
    return {
        "messages": [
            AIMessage(
                content=msg,
                additional_kwargs={"function_call": {"name": "collect_info", "arguments": json.dumps(kwargs)}},
            )
        ]
    }

def collect_info_tool(onboardService):
    return StructuredTool.from_function(
        func=collect_info,
        name="collect_info",
        description="Collects the information from the user, must collect all information required for onboarding",
        return_direct=False,
        args_schema=onboardService.serviceArgSchema,
    )

def confirm_information(state):
    """Confirm the information the user has provided and see if the user wants to continue or abort the onboarding process"""
    messages = state["messages"]
    service, _ = get_service_and_feature_from_messages(messages)
    if not service or service == "":
        raise ValueError("Service is not provided.")
    user_data = get_user_data(messages)
    if has_all_info(service, user_data) == "":
        msg = "Thanks for providing all the information. Do you want to continue the onboarding(yes/no) or update the information?"
    else:
        missing_field = has_all_info(service, user_data)
        msg = f"Still need to collect information for {missing_field}."
    return {
        "messages": [
            AIMessage(
                content=msg,
                additional_kwargs={"service": service, "need_confirm": "yes"},
            )
        ]
    }    

def onboard_service(state, onboardService):
    """Onboards the user to the service"""
    messages = state["messages"]
    service, _ = get_service_and_feature_from_messages(messages)
    if not service or service == "":
        raise ValueError("Service is not provided.")
    user_data = get_user_data(messages)
    if not user_data or len(user_data) == 0:
        msg = "No user data provided."
    else:
        msg = f"You are onboarding to {service} with the following information:\n \n " + " \n".join([f"{key}: {value}" for key, value in user_data.items()]) + " \n\n Once it is completed, you will be notified."
        asyncio.run(onboardService.onboard(user_data))
        state["messages"].clear()
    return {
        "messages": [
            AIMessage(
                content=msg,
                additional_kwargs={"onboard_status": "completed", "service": service}
            )
        ]
    }

def onboard_abort(state):
    """Aborts the onboarding process"""
    messages = state["messages"]
    service, _ = get_service_and_feature_from_messages(messages)
    if not service or service == "":
        raise ValueError("Service is not provided.")
    state["messages"].clear()
    return {
        "messages": [
            AIMessage(
                content=f"Onboarding process for {service} has been aborted. Please let me know if you need any other help.",
                additional_kwargs={"onboard_status": "completed", "service": service}
            )
        ]
    }

def get_confirm_messages(messages):
    sys_msg = """
    Your job is to help identify if the user want to continue or abort the onboarding process. 
    For other options, tell them to provide the correct choice (yes or no).
    """   
    messages = [SystemMessage(content=sys_msg)] + messages
    return messages

def get_user_data(messages):
    user_data = {}
    for message in messages:
        if "function_call" in message.additional_kwargs and message.additional_kwargs["function_call"]["name"] == "collect_info":
            data = json.loads(message.additional_kwargs["function_call"]["arguments"])
            user_data.update(data)
    return user_data

def need_confirm(messages):
    service, _ = get_service_and_feature_from_messages(messages)
    for message in messages[::-1]:
        if "need_confirm" in message.additional_kwargs and message.additional_kwargs["need_confirm"] == "yes":
            svc = message.additional_kwargs["service"]
            if svc and svc != "" and svc == service:
                return True
    return False


def call_model(state, model, base_model):
    messages = state["messages"]
    thread_id = state["thread_id"]
    service, feature = get_service_and_feature_from_messages(messages)
    last_message = messages[-1]
    confirm = need_confirm(messages)
    if confirm and isinstance(last_message, HumanMessage):
        _llm = base_model.bind_functions(functions=[convert_to_openai_function(t) for t in [confirm_onboarding]], function_call="confirm_onboarding")
        chain = get_confirm_messages | _llm
        response = chain.invoke([HumanMessage(content = last_message.content)])
    else:
        response = model.invoke(messages)
 
    cur_service, cur_feature = state["service"], state["feature"]
    if service and service != "" and feature and feature != "" and cur_service and cur_service != "" and cur_feature and cur_feature != "":
        if cur_service != service or cur_feature != feature:
            thread_id = str(uuid.uuid4())
    return {"messages": [response], "service": service, "feature": feature, "thread_id": thread_id}

    # Define the function to execute tools
def call_tool(state, tool_executor):
    messages = state["messages"]
    service, feature = get_service_and_feature_from_messages(messages)
    thread_id = state["thread_id"]
    
    last_message = messages[-1]
    action = ToolInvocation(
        tool=last_message.additional_kwargs["function_call"]["name"],
        tool_input=json.loads(
            last_message.additional_kwargs["function_call"]["arguments"]
        ),
    )
    
    response = tool_executor.invoke(action)
    
    function_message = FunctionMessage(content=str(response), name=action.tool)
    
    cur_service, cur_feature = state["service"], state["feature"]
    if service and service != "" and feature and feature != "" and cur_service and cur_service != "" and cur_feature and cur_feature != "":
        if cur_service != service or cur_feature != feature:
            thread_id = str(uuid.uuid4())
    return {"messages": [function_message], "service": service, "feature": feature, "thread_id": thread_id}