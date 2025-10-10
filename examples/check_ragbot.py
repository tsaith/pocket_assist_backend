import os
from dotenv import load_dotenv
from assistbot.robots.ragbot.bot_builder import BotBuilder

load_dotenv()

user_id = "1"

bot_builder = BotBuilder()
bot = bot_builder.build(user_id)
print("notebook_path: ", bot.notebook_path)

user_msg = "小八幾歲?"
ai_msg = bot.chat(user_msg)
print("user_msg: ", user_msg)
print("ai_msg: ", ai_msg)

user_msg = "誰喜歡小八?"
ai_msg = bot.chat(user_msg)
print("user_msg: ", user_msg)
print("ai_msg: ", ai_msg)

user_msg = "他擅長什麼?"
ai_msg = bot.chat(user_msg)
print("user_msg: ", user_msg)
print("ai_msg: ", ai_msg)