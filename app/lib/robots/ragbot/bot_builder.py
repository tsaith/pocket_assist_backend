
import os
from .ragbot import RAGBot
from .utils import get_notebook_path
class BotBuilder:

    def __init__(self):
        
        self.bots = {}

    def build(self, user_id: str):

        if user_id in self.bots:
            return self.bots[user_id]
        
        notebook_path = get_notebook_path(user_id)
        
        if not os.path.exists(os.path.dirname(notebook_path)):
            os.makedirs(os.path.dirname(notebook_path))
            
        if not os.path.exists(notebook_path):
            with open(notebook_path, 'w', encoding='utf-8') as f:
                f.write("我的筆記本。\n")

        bot = RAGBot()
        bot.init(user_id, notebook_path)
        self.bots[user_id] = bot
        
        return bot
