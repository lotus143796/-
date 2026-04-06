import openai

# 配置你的 DeepSeek API


def call_llm(prompt):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# 测试
prompt = """你是一个代码审查助手，你有一个工具叫做linter，用来检查代码的语法.
用户会给你代码
当收到代码后，你要调用工具，必须遵从下面的输出格式：
Action: linter
Action Input: 要检查的代码

当有了最终的答案，请输出：
Final Answer: 审查结论

注意：
-不要输出任何多余的东西
"""

result = call_llm(prompt)
print("原始输出：")
print(repr(result))
print("\n格式化输出：")
print(result)