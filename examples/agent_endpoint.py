

from dotenv import load_dotenv
load_dotenv()

# Install OS, JSON, and OpenAI libraries.
import os
import json
from openai import OpenAI

# Set your agent endpoint and access key as environment variables in your OS.
agent_endpoint = os.getenv("DIGITALOCEAN_ENDPOINT") + "/api/v1/"
agent_access_key = os.getenv("DIGITALOCEAN_API_KEY")

if __name__ == "__main__":
    client = OpenAI(
        base_url = agent_endpoint,
        api_key = agent_access_key,
    )

    response = client.chat.completions.create(
        model = "n/a",
        messages = [{"role": "user", "content": "你好，我是小明，请帮我写一个关于AI的论文，要求如下：1. 论文题目：AI在医疗领域的应用；2. 论文要求：论文需要包含AI在医疗领域的应用现状、存在的问题以及未来的发展趋势；3. 论文格式：论文需要按照学术论文的格式要求进行撰写。"}],
        extra_body = {"include_retrieval_info": True}
    )

# Prints response's content and retrieval object.
    for choice in response.choices:
        print(choice.message.content)

    response_dict = response.to_dict()

    print("\nFull retrieval object:")
    print(json.dumps(response_dict["retrieval"], indent=2)) 
 
