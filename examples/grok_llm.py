import getpass
import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
  os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")

model = init_chat_model("llama-3.3-70b-versatile", model_provider="groq")

print(model.invoke("請自我介紹"))