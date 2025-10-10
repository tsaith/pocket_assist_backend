
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
print("XAI_API_KEY:", os.getenv("XAI_API_KEY"))
