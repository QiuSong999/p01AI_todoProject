# 从 DeepSeek 客户端模块导入 client，用于调用大模型API

from ai.client import client

# 从 tools 模块导入 AI 查询工具函数
# 这些函数是真正执行数据库查询的业务工具
from ai.tools import (          #从 ai.tools 模块导入AI查询Todo时使用的5个工具函数。
    search_todos_by_title,       # 根据标题关键词查询Todo
    search_all_todos,            # 查询全部Todo
    search_todos_by_status,      # 根据状态查询Todo
    search_todos_by_deadline,    # 根据截止时间范围查询Todo
    search_todos_advanced,        # 根据多个条件组合查询Todo（标题、状态、时间范围）
    ai_tools                     #导入大模型可用的工具列表
)

from ai.prompt import search_prompt,search_user_prompt,search_result_prompt     #从 prompt 模块导入查询流程中使用的三个 prompt
# search_prompt：告诉AI如何选择查询工具
# search_user_prompt：提供当前时间和用户的查询需求
# search_result_prompt：告诉AI如何根据工具执行结果生成最终回答


from schema import AITodoSearch     # 导入Pydantic模型，用于校验AI返回的查询参数
from pydantic import ValidationError

# FastAPI异常类，用于返回HTTP错误
from fastapi import HTTPException

# 用于JSON字符串和Python字典之间转换
import json

# 获取当前时间：用于让AI理解“今天、明天、后天”等时间表达
from datetime import datetime

### 1、公共辅助函数(把下面的重复代码抽取出来)
# 把AI返回的查询参数解析和校验逻辑抽取出来。避免 search_todos_by_title、search_all_todos、
# search_todos_by_status 三个分支重复写相同代码。

##公共参数解析函数
def parse_ai_search_arguments(tool_call):       #tool_call是第一次调用 AI 后，AI 返回的工具调用信息。
    try:
        arguments = json.loads(tool_call.function.arguments)    #tool_call.function.argumentsAI 返回的工具参数
        #拿出来后就是 '{"title":"牛肉","page":1,"page_size":10}'这种json字符串，把他转化为字典{"title":"牛肉","page":1,"page_size":10}

        return AITodoSearch(**arguments)    #把 AI 返回的参数字典，转换成 AITodoSearch 对象，并顺便校验数据。
        #**arguments把上面字典{"title":"牛肉","page":1,"page_size":10} 拆开: title="牛肉",page=1,page_size=10
        # **字典 = 把字典里的键值对拆成 参数名=参数值
        #AITodoSearch(...)：创建对象，最后得到AITodoSearch(title="牛肉",page=1,page_size=10)
        # schema.py里的：class AITodoSearch(BaseModel):在定义规则。 AITodoSearch(**arguments)是在按照这个规则创建一个实际对象（校验）。

    except (json.JSONDecodeError, ValidationError) as e:
        #捕获json.JSONDecodeError（JSON格式错误）和（ValidationError：不满足AITodoSearch）2种错误
        raise HTTPException(
            status_code=400,
            detail="ai query parameters invalid"
        ) from e


### 2、AI工具选择函数
# 作用：第一次调用AI，让AI根据用户需求选择应该执行哪个工具，并生成工具参数
def ask_deepseek_tool(messages):  # 让AI选择工具
    """
    第一次调用 DeepSeek。
    作用：
        不是直接回答用户问题，
        而是让 AI 判断：
        1. 用户想查询什么
        2. 应该调用哪个工具
        3. 调用工具时需要传什么参数

    流程：
        用户问题
            ↓
        DeepSeek
            ↓
        选择工具 + 生成参数
            ↓
        Python执行对应函数
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,  # 发送给AI的上下文消息，本函数要上传的参数
            tools=ai_tools,     #ai_tools 是从tools.py文件导入的大模型可用的工具列表（5个工具）

            tool_choice="auto"  # 让AI自己决定是否调用工具
        )

        return response.choices[0].message
        # 返回AI生成的消息对象。里面可能包含：
        # 1.content 普通回答
        # 2.tool_calls AI选择的工具

    except Exception as e:
        print("ai service error:", e)
        raise Exception(f"ai service error: {e}") from e
"""
用户：
"帮我查一下没完成的任务"
        ↓
searchtodo_by_AI()
        ↓
      调用
        ↓
ask_deepseek_tool()
        ↓
    DeepSeek判断：
    假如要调用：
    get_pending_todos
    参数：
    {
     page:1,
     page_size:10
    }
        ↓
返回给 searchtodo_by_AI()
        ↓
Python执行真正查询
        ↓
      MySQL
~~~~~~~   
所以：ask_deepseek_tool = AI决策阶段
"""

### 3、 定义AI查询Todo/数据 的业务函数
def searchtodo_by_AI(message):
    """
    AI查询Todo主流程。
    完整流程如下：
        用户：
            "查找买相关的待办"
                ↓
        第一次调用AI：
            判断调用哪个工具
                ↓
        Python执行工具：
            查询MySQL
                ↓
        第二次调用AI：
            把查询结果整理成人类语言
                ↓
        返回用户
    """
    now_time = datetime.now()
    prompt = search_user_prompt(message, now_time)      #导入生成本次AI查询的用户提示词
    # 把当前时间和用户的问题传给AI，帮助AI理解“今天、明天、后天”等时间表达

    messages = [{"role": "system",
                 "content": search_prompt() },  #search_prompt()：生成“AI查询Todo时选择工具”的提示词
                #告诉AI：你有哪些查询工具。根据用户需求选择对应工具。

                {"role": "user",
                 "content": prompt}]

    result = ask_deepseek_tool(messages)  # 上面message填充后作为参数传给ask_deepseek_tool，即执行AI工具选择函数。
    # 第一次调用AI.目的：让AI决定应该调用哪个工具
    """
    result大概是如下结果：
           {
       "role": "assistant",
       "content": None,
       "tool_calls": [
           {
               "id": "call_xxx",
               "type": "function",
               "function": {
                   "name": "search_todos_by_status",
                   "arguments": "{\"status\":\"pending\",\"page\":1,\"page_size\":10}"
            }}],
            ……
    
    """

    print("AI返回：", result)

    if not result.tool_calls:       #如果生成的工具列表为空
        raise HTTPException(
            status_code=400,
            detail="无法识别查询需求"
        )  # 没有工具：[] → 返回400错误：无法识别查询需求


    print("AI选择的工具：", result.tool_calls)  # 第一次调用AI是让AI得到需要用到的Tools
    # result.tool_calls 即从AI返回的response 中取出tool_calls(所用的工具)

    tool_call = result.tool_calls[0]  # tool_calls = 工具调用列表
    # result.tool_calls = [工具调用1,工具调用2,工具调用3]      #这种结构
    print("工具名称：", tool_call.function.name)             #打印所用工具的名字
    print("工具参数：", tool_call.function.arguments)        #打印所用工具的参数


    # -------------根据AI选择的工具执行不同函数-------------
    # 工具1
    if tool_call.function.name == "search_todos_by_title":      #如果是根据title查询相关数据
        search_data = parse_ai_search_arguments(tool_call)  #得到对象如：AITodoSearch(title="牛肉",page=1,page_size=10)
        # 引用###5步骤里面的公共参数解析函数：
        # 1. 解析AI返回的JSON参数
        # 2. 使用AITodoSearch进行参数校验
        # 3. 校验失败时统一返回400错误
        """
         原版：
             if tool_call.function.name == "search_todos_by_title":
                 try:
                     arguments = json.loads(tool_call.function.arguments)
                     # AI返回的参数是JSON字符串例如：'{"page":1,"page_size":5}'，把它转换成Python字典
                     search_data = AITodoSearch(**arguments)     #search_data 是 AITodoSearch 对象
                 except (json.JSONDecodeError, ValidationError) as e:
                     raise HTTPException(
                         status_code=400,
                         detail="ai query parameters invalid"
                     ) from e
            现在被上面parse_ai_search_arguments函数取代
         """

        #search_data是AITodoSearch校验后得到的其对象
        title = search_data.title       #取出上面得到对象的title
        query_result = search_todos_by_title(title ,search_data.page ,search_data.page_size)    # 执行真正的查询

    # 工具2~~~~~~
    elif tool_call.function.name == "search_all_todos":
        search_data = parse_ai_search_arguments(tool_call)

        query_result = search_all_todos(
            search_data.page,
            search_data.page_size
        )  # 调用工具2，执行真正的查询

    # 工具3~~~~~~
    elif tool_call.function.name == "search_todos_by_status":
        search_data = parse_ai_search_arguments(tool_call)

        status = search_data.status

        query_result = search_todos_by_status(      #调用工具3
            status,
            search_data.page,
            search_data.page_size
        )

    # 工具4~~~~~~
    elif tool_call.function.name == "search_todos_by_deadline":
        arguments = parse_ai_search_arguments(tool_call)    #arguments 已经不是普通字典，而是 AITodoSearch 对象

        query_result = search_todos_by_deadline(
            arguments.start_time,
            arguments.end_time,
            arguments.page,
            arguments.page_size
        )

    # 工具5
    elif tool_call.function.name == "search_todos_advanced":
        arguments = parse_ai_search_arguments(tool_call)

        query_result = search_todos_advanced(
            title=arguments.title,
            status=arguments.status,
            start_time=arguments.start_time,
            end_time=arguments.end_time,
            page=arguments.page,
            page_size=arguments.page_size
        )

    ##5个查询工具执行完成后，统一处理查询结果
    # 离开 if / elif → 统一处理参数
    todos = query_result["data"]                      # 当前页查询到的Todo数据
    total = query_result["total"]                     # 符合条件的总数量

    current_page = query_result["page"]               # 当前页码
    current_page_size = query_result["page_size"]     # 每页数量

    total_pages = (total + current_page_size - 1) // current_page_size
    # 计算总页数。例如：total=7，page_size=5。结果：2页
    print("工具执行结果：", todos)

    # ~~~~~~~~~上面第一次调用AI，让AI确定执行哪个函数（工具），并得到返回结果~~~~~~~~~
    """
    第一次调用AI：让 AI 决定“调用哪个工具”（这里必须把 tools 告诉 AI。所以第一次需要：messages + tools）
    第二次：已经没有“选工具”这个任务了，根据查询结果回答用户即可（不需要再传 tools）
    """
    # ~~~~~~~~~~~~~~~下面第二次调用AI，让AI把查询到的结果组织给我们~~~~~~~~~~~~~~~~~

    # 创建工具执行结果消息，Python执行AI选择的工具后，把查询数据库的结果包装成 AI 能理解的tool消息。
    # 让第二次AI根据这个结果生成最终回答。
    tool_message = {
        "role": "tool",  # 告诉AI：这条消息不是用户输入，也不是AI回答，而是Python执行工具后的返回结果。
        "tool_call_id": tool_call.id,  # 表示这条工具结果对应第一次AI调用的哪个工具。
        "content": str({  # 保存Python查询数据库后的结果，发送给第二次AI。
            "data": todos,
            "total": total,
            "page": current_page,
            "page_size": current_page_size,
            "total_pages": total_pages})
    }  # 把查到的数据放进工具消息里
    # 把 Python 执行工具得到的结果，包装成一条 AI 能看懂的“工具结果消息”，准备下一步发送给 AI

    # 第二次调用AI需要的完整上下文消息（上面的tool_message要拼接到messages里）
    # 包含：系统要求、用户原始问题、第一次AI选择工具的结果、Python执行工具后的查询结果
    messages = [{  # 重新构造第二次AI需要的消息
        "role": "system",
        "content":search_result_prompt()},
        result,  # 第一次AI选择工具的结果
        tool_message]  # Python执行工具后的结果

    second_response = client.chat.completions.create(  # 第二次调用AI
        model="deepseek-flash",
        messages=messages)
    # 这次不负责选择工具。只根据tool_message里的查询结果，整理成人类能看懂的回答。

    final_message = second_response.choices[0].message.content

    print("第二次AI最终回答：", final_message)

    return {"message": final_message,
            "page" :current_page,  # 当前第几页
            "page_size": current_page_size,  # 每页多少条
            "total": total,  # 符合查询条件的全部数据有多少条
            "total_pages": total_pages,  # 全部数据一共多少页
            "data": todos}  # 当前这一页的数据

"""
现在的 AI 查询分成3条路线
① 按标题关键词查询数据：
用户：
    "帮我找一下买牛肉相关的待办"
             ↓
        DeepSeek
             ↓
       AI分析用户需求
             ↓
       选择查询工具：
       search_todos_by_title
             ↓
      生成工具参数：
      {
        "title": "牛肉",
        "page": 1,
        "page_size": 10
     }
             ↓
    Python执行工具函数：
    search_todos_by_title(
        title,
        page,
        page_size
    )
             ↓
        db.py数据库函数
             ↓
        MySQL执行SQL：
    where title like "%牛肉%"
             ↓
        返回查询结果
             ↓
    第二次调用DeepSeek
             ↓
        AI整理查询结果
             ↓
        返回用户

②查询所有数据
    ……
③按执行状态查询数据
    ……
④按deadline查询数据
    ……
⑤复合查询数据
    ……
"""
"""
①searchtodo_by_AI(): 负责整个查询流程，相当于“总经理”。
②ask_deepseek_tool(): 负责问 AI：“用户想干什么？应该用哪个工具？”
③search_todos_by_title(): 负责真正干活：“去数据库查未完成任务”。

它们的调用关系：
    用户问题 → searchtodo_by_AI() → ask_deepseek_tool() → AI选择工具 →
    → search_todos_by_title() →  db.py  →  MySQL
"""