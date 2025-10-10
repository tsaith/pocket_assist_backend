import os
from typing import TypedDict, Annotated
import operator
import requests
import json

from langchain.chat_models import init_chat_model
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain_xai import ChatXAI

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langgraph.checkpoint.memory import MemorySaver

class State(TypedDict):
    messages: Annotated[list, add_messages]


@tool
def check_site_alive(site: str) -> bool:
    """Check a site is alive or not."""
    try:
        resp = requests.get(f'https://{site}')
        resp.raise_for_status()
        return True
    except Exception:
        return False

@tool
def add_numbers(a: int, b: int) -> int:
    """將兩個數字相加"""
    return a + b

tool = check_site_alive
tools = [tool]
tool_node = ToolNode(tools=tools)

memory = MemorySaver()

class ReactAgent:

    def __init__(self):

        # Model: "gpt-4o-mini", "gpt-4o", "grok-beta"
        model = "gpt-4o-mini" 
        #model = "grok-beta"

        if model.startswith("gpt"):
            model_provider = "openai"
            api_key = os.getenv("OPENAI_API_KEY")
        elif model.startswith("grok"):
            model_provider = "xai"
            api_key = os.getenv("XAI_API_KEY")

        '''
        model_provider = "xai"
        api_key = os.getenv("XAI_API_KEY")
        '''

        self.llm = init_chat_model(
            model=model,
            model_provider=model_provider,
            api_key=api_key,
        )

        self.llm_with_tools = self.llm.bind_tools(tools)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant with long-term memory. \
              Use past interactions to assist the user naturally. \
              Use traditional Chinese to chat with user."),
            ("placeholder", "{messages}")
        ]) 

        self.agent = create_react_agent(
            model=self.llm,
            prompt=prompt,
            tools=tools,
            checkpointer=memory,
        )
        '''
        graph_builder = StateGraph(State)
        graph_builder.add_node("chatbot", self.chatbot)
        graph_builder.add_node("tools", tool_node)

        graph_builder.add_conditional_edges(
            "chatbot",
            tools_condition,
        )

        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_edge("chatbot", "tools")
        self.graph = graph_builder.compile(checkpointer=memory)
        '''

    def chatbot(self, state: State) -> State:
        return {"messages": [self.llm_with_tools.invoke(state["messages"])]}

    def llm_invoke(self, text: str):
        human_message = HumanMessage(content=text)
        response = self.llm.invoke([human_message])
        return response

    def reply(self, thread_id: str, text: str):

        config = {"configurable": {"thread_id": thread_id}}
        human_message = HumanMessage(content=text)

        response = self.agent.invoke(
            {"messages": [human_message]}, config=config
        )

        ai_message = response["messages"][-1].content
        return ai_message


if __name__ == "__main__":
    bot = ReactAgent()
    print(bot.reply("123", "請介紹您自己"))
