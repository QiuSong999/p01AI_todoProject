"""ai大模型总入口"""

from ai.client import ask_deepseek       # 从 ai 包的 client.py 文件中导入
# client：DeepSeek客户端对象，用于直接调用大模型API
# ask_deepseek：封装好的普通AI调用函数，用于发送消息并获取AI返回结果

from ai.prompt import intent_prompt     #从ai.prompt模块导入意图识别提示词函数
# intent_prompt()专门负责生成“判断用户操作(add/update/delete/search)”的system prompt。


import json     #为了把json格式转为dict字典格式

from schema import AIAction

from ai.todo import (       # 从ai.todo模块导入 AI操作Todo数据的业务函数。
    addtodo_by_AI,          #根据用户自然语言，调用AI解析后新增Todo。
    updatetodo_by_AI,       #根据用户自然语言，调用AI解析后修改Todo。
    deletetodo_by_AI        #根据用户自然语言，调用AI匹配后删除Todo。
)
from ai.search import searchtodo_by_AI  #根据用户自然语言，调用AI匹配后查询Todo。

"""
ask_deepseek()         ask_deepseek_tool()  
        ↓                      ↓  
普通 JSON AI 调用          Tool Calling      
        ↓                      ↓    
新增 / 修改 / 删除             AI 查询      
"""

### 1、定义AI判断用户意图函数
def ai_chat(message):
    result = ask_deepseek(intent_prompt(message))     #调用DeepSeek，让AI根据用户输入判断用户想执行的操作。
    # intent_prompt(message)负责生成发送给AI的提示词(prompt)。内容是让AI输出如'{"action": "search","content": "帮我查一下没完成的任务"}'
    # ask_deepseek()负责真正调用DeepSeek API，返回结果是AI生成的JSON字符串。

    result = json.loads(result)
    action = AIAction(**result)
    #校验AI输出的格式是否满足AIAction，如action={"action": "search","content": "帮我查一下没完成的任务"}
    #并把输出结果变成AIAction对象AIAction("action": "search","content": "帮我查一下没完成的任务")

    return action


### 2、AI总入口函数
def todo_by_AI(message):
    action = ai_chat(message)   #执行上面的AI判断意图函数，得出用户想操作的动作（增/删/改/查）
    # 例如ai_chat(message)输出：action = {"action": "search", "content": "帮我查一下没完成的任务"}

    # action = add / update / delete / search
    if action.action == "add":
        result = addtodo_by_AI(action.content)      #AI增
        #把用户输入的消息，当作参数传给addtodo_by_AI(用户输入的消息)

    elif action.action == "update":
        result = updatetodo_by_AI(action.content)   #AI改

    elif action.action == "delete":
        result = deletetodo_by_AI(action.content)   #AI删

    elif action.action == "search":
        result = searchtodo_by_AI(action.content)  #AI查



    return result

"""
 用户一句话
    ↓
todo_by_AI()
    ↓
 ai_chat()
    ↓
  AI判断
    ↓
 AIAction
    ↓
根据action选择:

add      → addtodo_by_AI()
update   → updatetodo_by_AI()
delete   → deletetodo_by_AI()
search   → searchtodo_by_AI()
"""
















