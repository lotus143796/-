import openai

SYSTEM_PROMPT = """你是一个代码审查助手，你有一个工具叫做linter，用来检查代码的语法.
用户会给你代码
当收到代码后，你要调用工具，必须遵从下面的输出格式：
Action: linter
Action Input: 要检查的代码

当你从工具获取结果后，判断：
-如果结果已经可以返回用户，输出Final Answer
-如果不可以的话继续调用工具
注意：
-不要输出任何多余的东西
"""

client = openai.OpenAI(
    api_key="sk-e3eeabcb32d94af5a066b63e7faefa24",
    base_url="https://api.deepseek.com"
)
class SimpleAgent:
    def __init__(self,llm_function,max_steps=5):
        self.llm_function = llm_function
        self.max_steps = max_steps
        self.tools={}

    def register_tool(self,name,function):
        self.tools[name] = function

    def run(self,question):

        steps=0
        memory=[]
        while steps < self.max_steps:

            if memory:
                full_input = question + "\n\n" + "\n".join(memory)
            else:
                full_input = question
            print("发送给 LLM 的内容：", repr(full_input))  # 加这行
            answer = self.llm_function(full_input)
            print("LLM 返回：", repr(answer))
            memory.append(answer)
            if "Final Answer" in answer:
                result=answer.split("Final Answer:")[1].strip()
                return result
            if "Action:" in answer:
                tool_name=answer.split("Action:")[1].split("\n")[0].strip()
                tool_input=answer.split("Action Input:")[1].strip()


                if tool_name in self.tools:
                    observation=self.tools[tool_name](tool_input)
                    memory.append(f"工具已执行，结果：{observation}")
                else :
                    print("没有这个工具")


            steps+=1
        return "达到最大步数，未完成"

def call_llm(prompt):
    full_prompt=SYSTEM_PROMPT+prompt
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0
    )
    return response.choices[0].message.content

def linter(code):
    if "print" in code:
        return "发现print语句"
    return "未发现print语句"

def find_pattern(code, pattern, comment_marker):
    codes = code.split("\n")
    s = []
    num = 1
    for co in codes:
        if co == '':
            continue
        elif co[0] == comment_marker:
            continue
        elif  pattern in co:
            s.append(num)
        num += 1
    return s

python_code = 'print("a")\n# comment\nprint("b")'
java_code = 'System.out.println("a");\n// comment\nSystem.out.println("b");'

print(find_pattern(python_code, "print", "#"))        # [1, 3]
print(find_pattern(java_code, "System.out.println", "//"))  # [1, 3]




