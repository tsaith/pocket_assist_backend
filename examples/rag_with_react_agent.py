import os
import operator
import requests
import json

os.environ['USER_AGENT'] = 'myagent'

from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict, Annotated, List, Sequence, Literal
from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model

from langchain_core.tools import tool
from langchain_core.messages import (
    HumanMessage, AIMessage
)

from langgraph.graph import StateGraph, START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chat_models import init_chat_model

note_path = "./data/1/personal/note.txt"
loader = TextLoader(note_path)
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

embeddings = OpenAIEmbeddings()
vector_store = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings())
retriever = vector_store.as_retriever()

@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=1)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

tools = [retrieve]

llm = init_chat_model("gpt-4o-mini", model_provider="openai")
memory = MemorySaver()

agent_executor = create_react_agent(model=llm, tools=tools, checkpointer=memory)

def chat(user_id, user_msg):

    # Specify an ID for the thread
    config = {"configurable": {"thread_id": user_id}}
    
    response = agent_executor.invoke(
        {"messages": [{"role": "user", "content": user_msg}]}, config=config
    )
    ai_msg = response["messages"][-1].content

    return ai_msg

user_id = "1"

user_msg = "小八幾歲?"
ai_msg = chat(user_id, user_msg)
print("user_msg: ", user_msg)
print("ai_msg: ", ai_msg)

user_msg = "誰喜歡小八?"
ai_msg = chat(user_id, user_msg)

print("user_msg: ", user_msg)
print("ai_msg: ", ai_msg)

user_msg = "小九幾歲?"
ai_msg = chat(user_id, user_msg)

print("user_msg: ", user_msg)
print("ai_msg: ", ai_msg)
