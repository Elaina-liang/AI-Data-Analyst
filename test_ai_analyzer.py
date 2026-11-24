
import pandas as pd
from core.ai_analyzer import ask_deepseek

# 构造一份模拟数据
df = pd.DataFrame({
    "专业": ["计算机科学", "计算机科学", "数据科学", "数据科学"],
    "成绩": [90, 85, 88, 92]
})

# 生成数据摘要
data_context = f"""
数据行数：{len(df)}
平均成绩：{df['成绩'].mean():.2f}
最高成绩：{df['成绩'].max()}
最低成绩：{df['成绩'].min()}

各专业平均成绩：
{df.groupby('专业')['成绩'].mean().to_string()}
"""

# 向 AI 提问
question = "哪个专业的平均成绩更高？请解释计算依据。"

result = ask_deepseek(question, data_context)

print("AI 分析结果：")
print(result)
