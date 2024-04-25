from agents.launchdarkly_learningpath_tool import LaunchDarklyLearningPathTool
from agents.github_learningpath_tool import GitHubLearningPathTool
from agents.snyk_learningpath_tool import SnykLearningPathTool
from agents.instant_tools import lookup_learningobjects
from langchain_core.messages import HumanMessage
import streamlit as st
import time
import re
import uuid
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from agents.github_onboard_service import GitHubOnboardService
from agents.launchdarkly_onboard_service import LaunchDarklyOnboardService
from agents.snyk_onboard_service import SnykOnboardService
from langchain_openai import ChatOpenAI
from graphs.main_workflow import MainWorkflow
from utils.base_service_query import BaseServiceQuery
from langchain_community.tools.tavily_search import TavilySearchResults
import nest_asyncio
from dotenv import load_dotenv
from configs import Configs

def main():
   
    load_dotenv(dotenv_path="application.env")
    
    nest_asyncio.apply()
    memory = SqliteSaver(conn=sqlite3.connect(":memory:", check_same_thread=False))
    router_model = ChatOpenAI(model_name=Configs.general_configs()["router_model"], temperature=0)
    service_model = ChatOpenAI(model_name=Configs.general_configs()["service_model"], temperature=0)
    thread_id = str(uuid.uuid4())
    
    github_onboarding_service = GitHubOnboardService(service="github")
    launchdarkly_onboarding_service = LaunchDarklyOnboardService(service="launchdarkly")
    snyk_onboarding_service = SnykOnboardService(service="snyk")
    
    github_learningpath_tool = GitHubLearningPathTool()
    launchdarkly_learningpath_tool = LaunchDarklyLearningPathTool()
    snyk_learningpath_tool = SnykLearningPathTool()
    
    search_tool = TavilySearchResults()
    
    github_query = BaseServiceQuery(service="github")
    github_retriever_tool = github_query.build_retriever_tool(name="GitHubServiceQuery", description="Query documentation and answer question for GitHub service")
    
    launchdarkly_query = BaseServiceQuery(service="launchdarkly")
    launchdarkly_retriever_tool = launchdarkly_query.build_retriever_tool(name="LaunchDarklyServiceQuery", description="Query documentation and answer question for LaunchDarkly service")
    
    snyk_query = BaseServiceQuery(service="snyk")
    snyk_retriever_tool = snyk_query.build_retriever_tool(name="SnykServiceQuery", description="Query documentation and answer question for Snyk service")
    
    main_workflow = MainWorkflow(llm=router_model, memory=memory)
    main_workflow.register_onboarding_service(service="github", onboard_svc=github_onboarding_service, llm=service_model)
    main_workflow.register_onboarding_service(service="launchdarkly", onboard_svc=launchdarkly_onboarding_service, llm=service_model)
    main_workflow.register_onboarding_service(service="snyk", onboard_svc=snyk_onboarding_service, llm=service_model)
    
    main_workflow.register_learningpath_service(service="github", prompt_path="prompts/templates/learningpath.txt", prompt_data={"service": "GitHub"}, tools=[lookup_learningobjects, github_learningpath_tool], llm=service_model)
    main_workflow.register_learningpath_service(service="launchdarkly", prompt_path="prompts/templates/learningpath.txt", prompt_data={"service": "LaunchDarkly"}, tools=[lookup_learningobjects, launchdarkly_learningpath_tool], llm=service_model)
    main_workflow.register_learningpath_service(service="snyk", prompt_path="prompts/templates/learningpath.txt", prompt_data={"service": "Snyk"}, tools=[lookup_learningobjects, snyk_learningpath_tool], llm=service_model)
    
    main_workflow.register_query_service(service="launchdarkly", prompt_path="prompts/templates/query.txt", prompt_data={"service": "GitHub"}, tools=[search_tool, launchdarkly_retriever_tool], llm=service_model)
    main_workflow.register_query_service(service="github", prompt_path="prompts/templates/query.txt", prompt_data={"service": "LaunchDarkly"}, tools=[search_tool, github_retriever_tool], llm=service_model)
    main_workflow.register_query_service(service="snyk", prompt_path="prompts/templates/query.txt", prompt_data={"service": "Snyk"}, tools=[search_tool, snyk_retriever_tool], llm=service_model)
    
    graph = main_workflow.build_graph()
    
    config = {"configurable": {"thread_id": thread_id}}
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "workflow" not in st.session_state:
        st.session_state.workflow = main_workflow
        
    if "graph" not in st.session_state:
        st.session_state.graph = graph
    
    if "config" not in st.session_state:
        st.session_state.config = config
    
    if "prev_msgs" not in st.session_state:
        st.session_state.prev_msgs = []

    st.title("Onboarding to SaaS based engineering tools")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if user_input := st.chat_input("Tell me what do you want to do?"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            st.session_state.workflow.update_state_after_onboarding(st.session_state.config)
            print("\n*** Thread ID:  " + st.session_state.config["configurable"]["thread_id"] + "****\n")
            response = st.session_state.graph.invoke({"messages": st.session_state.prev_msgs + [HumanMessage(content=user_input)], "thread_id": st.session_state.config["configurable"]["thread_id"]}, config=st.session_state.config)
            st.session_state.workflow.update_state(st.session_state.config, st.session_state.prev_msgs)
            final_resp = ""
            # simulate streaming
            for chunk in re.split(r'(\s+)', response["messages"][-1].content):
                final_resp += chunk + " "
                time.sleep(0.01)
                message_placeholder.markdown(final_resp)
        st.session_state.messages.append({"role": "assistant", "content": response["messages"][-1].content})
    

if __name__ == "__main__":
    main()