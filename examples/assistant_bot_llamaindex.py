import os
from typing import TypedDict, Annotated
import operator
import requests
import json

from dotenv import load_dotenv

from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.workflow import Context
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.agent.openai import OpenAIAssistantAgent


load_dotenv()
llm = OpenAI(model="gpt-4o-mini")

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
knowledge_engine = index.as_query_engine(similarity_top_k=3)

query_engine_tools = [
    QueryEngineTool(
        query_engine=knowledge_engine,
        metadata=ToolMetadata(
            name="knowledge",
            description=(
                "Provides information about the domain knowledge of the company. "
                "Use a detailed plain text question as input to the tool."
            ),
        ),
    )
]

async def set_name(ctx: Context, name: str) -> str:
    state = await ctx.get("state")
    state["name"] = name
    await ctx.set("state", state)
    return f"Name set to {name}"


class AssistantBot:

    def __init__(self):

        # Model: "gpt-4o-mini", "gpt-4o", "grok-beta"
        model = "gpt-4o-mini" 
        #model = "grok-beta" 

        if model.startswith("gpt"):
            llm = OpenAI(model="gpt-4o-mini")
        elif model.startswith("grok"):
            llm = OpenAI(model="grok-beta")

        self.workflow = AgentWorkflow.from_tools_or_functions(
            [set_name],
            llm=llm,
            system_prompt="You are a helpful assistant.",
            initial_state={"name": "unset"}
        )

        self.ctx = Context(self.workflow)

        chat_engine = index.as_chat_engine(chat_mode="react", llm=llm, verbose=True)
        self.agent = chat_engine

    def chat(self, user_msg: str):

        response = self.agent.chat(user_msg)
        ai_message = str(response)

        return ai_message

