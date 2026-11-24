

import os
from dotenv import load_dotenv
from openai import OpenAI

# 读取 .env
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise RuntimeError("没有读取到 API Key，请检查 .env 文件")

# 创建 DeepSeek 客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 发送一次简短请求
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {
            "role": "system",
            "content": "你是一个简洁的数据分析助手。"
        },
        {
            "role": "user",
            "content": "请只回复：DeepSeek API 连接成功。"
        }
    ],
    max_tokens=50,
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    }
)

print("API 请求成功！")
print("AI 回复：", response.choices[0].message.content)
