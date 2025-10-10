import os
from dotenv import load_dotenv

from assistbot.agent.react_agent import AgentBot

load_dotenv()

agent = AgentBot()

user_id = "1"
#response = agent.reply(user_id, "請檢查今天 google 的網站是否掛掉了?")
#print("response: ", response)

for query in [
    "How are you?",
    "請檢查今天 google 的網站是否掛掉了?",
    "Bye."
]:
    ai_message = agent.reply(user_id, query)
    print(f"User: {query}")
    print(f"AI: {ai_message}\n")
