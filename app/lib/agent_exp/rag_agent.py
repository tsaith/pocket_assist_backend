import os
from typing import TypedDict, Annotated
import operator
import requests
import json

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

from dotenv import load_dotenv

load_dotenv()

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)

class RagAgent:

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

        self.agent = index.as_query_engine()

    def reply(self, thread_id: str, text: str):

        response = self.agent.query(text)

        return response


if __name__ == "__main__":
    bot = RagAgent()
    print(bot.reply("123", "請介紹您自己"))
