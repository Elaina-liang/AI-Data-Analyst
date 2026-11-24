
import os
from dotenv import load_dotenv
from openai import OpenAI

# 读取环境变量
load_dotenv()

def get_ai_client():
    """创建 DeepSeek API 客户端"""

    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise RuntimeError("未找到 DeepSeek API Key，请检查 .env 文件")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


def ask_deepseek(question, data_context):
    """
    向 DeepSeek 发送数据分析问题。

    question: 用户的问题
    data_context: 数据集的统计摘要，而不是完整数据
    """

    client = get_ai_client()

    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {
                "role": "system",
                "content": (
                    "请根据提供的数据统计信息回答问题。"
                    "必须区分统计计算结果与数据质量问题。"
                    "如果发现缺失值、重复记录或可能的异常值，"
                    "请主动提醒用户，并解释它们可能造成的影响。"
                    "不要擅自删除、修改或推测数据。"
                    "如果成绩超过100分，只能在百分制假设下提示可能异常。"
                    "不要把重复记录直接认定为不同学生或不同学生的错误记录。"
                    "不要编造数据；如果信息不足，请明确说明。"
                    "回答应清晰、简洁，并解释分析依据。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"数据摘要：\n{data_context}\n\n"
                    f"用户问题：{question}"
                )
            }
        ],
        max_tokens=800,
        extra_body={
            "thinking": {
                "type": "disabled"
            }
        }
    )

    return response.choices[0].message.content
