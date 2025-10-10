
import os
from assistbot.core.global_data import get_data_dir

def get_notebook_path(user_id: str, file_name: str = "notebook.txt"):

    data_dir = get_data_dir()
    file_path = os.path.join(data_dir, user_id, file_name)

    return file_path

