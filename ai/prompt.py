"""各种prompt"""

#~~~~~~~~~~~~~~~~~~意图识别类提示词~~~~~~~~~~~~~~~~~~
### 1、负责生成“判断用户操作(add/update/delete/search)”的提示词
# 作用：接收用户一句话,让AI判断用户想执行：增/删/改/查
#返回格式{"action":"add","content":"用户原话"}
def intent_prompt(message):
    return(
        "你是一个todo助手。"
        "判断用户想执行什么操作。"
        "只能返回json。"
        "action只能是add、update、delete、search。"
        "content返回用户原话。"
        f"用户输入：{message}")
    #让DeepSeek判断操作类型。


#~~~~~~~~~~~~~~~~~~查询类提示词~~~~~~~~~~~~~~~~~~
### 2、负责生成“AI查询Todo时选择工具”的提示词。
#作用：告诉AI：你有哪些查询工具。根据用户需求选择对应工具。
#这里不查询数据库。这里只负责告诉AI如何选择工具。
def search_prompt():
    return """
            你是一个Todo查询助手，根据用户需求选择合适的查询工具。
            
            规则：
                1. 如果用户查询标题关键词，调用 search_todos_by_title。
                2. 如果用户查询全部任务，调用 search_all_todos。
                3. 如果用户查询状态，例如未完成、已完成，调用 search_todos_by_status。
                4. 如果用户查询某个时间范围，例如：
                   - 今天有哪些任务
                   - 明天有哪些任务
                   - 后天有哪些任务
                   - 某日期有哪些任务
                    必须调用 search_todos_by_deadline。
                5. 如果用户同时提供多个查询条件：
                   调用 search_todos_advanced。

                   例如：
                   - 查询未完成的买牛肉任务
                   - 查询明天未完成任务
                   - 查询9月份pending任务
                
                deadline 查询需要生成：
                start_time:
                开始时间 YYYY-MM-DD 00:00:00
                
                end_time:
                结束时间 YYYY-MM-DD 23:59:59
                
                不要直接回答用户。
                必须选择工具。
            """

### 3、生成本次AI查询的用户提示词
#作用：把当前时间和用户的问题传给AI，帮助AI理解“今天、明天、后天”等时间表达
def search_user_prompt(message, now_time):
    #这个now_time程序会根据searchtodo_by_AI函数上方的now_time = datetime.now()，自动获取
    return f"""
    你是一个Todo查询助手。
    当前时间：
    {now_time}

    请根据当前时间理解用户的日期表达。
    例如：
    明天 = 当前日期的下一天。

    用户说：
    {message}
    """

### 4、查询结果返回Prompt
# 工具执行完成后，告诉AI如何根据查询结果生成最终回答
def search_result_prompt():

    return """
    工具已经执行完成。
    不要再次调用任何工具，只根据工具返回的数据回答用户。
    如果 total 为 0，明确告诉用户没有找到符合条件的待办事项。
    """

#~~~~~~~~~~~~~~~~~~Todo操作类提示词(增、删、改)~~~~~~~~~~~~~~~~~~
### 5、负责生成AI新增Todo提示词
#作用：让AI从用户自然语言中提取：title deadline，后续交给TodoAdd校验，然后写入数据库。
def add_prompt(message, now_time):
    return (
        "请根据用户的要求创建一个todo。"
        "返回json，必须包含title和deadline两个字段。"
        "deadline必须返回完整的日期时间，格式必须是YYYY-MM-DD HH:MM:SS。"
        f"当前时间是：{now_time}"
        f"用户要求：{message}"
    )

### 6、负责生成AI修改Todo提示词
#作用：第一次调用AI。只负责提取用户想修改的字段。
#不负责判断修改哪一条todo。找具体todo由第二次AI完成。
def update_prompt(message, now_time):
    return (
        "你是一个todo修改信息提取助手。"
        "你的任务是从用户的话中提取需要修改的字段。"
        "只返回json格式。"
        "如果用户要求修改deadline，则返回deadline字段。"
        "如果用户要求修改status，则返回status字段。"
        "不要返回title字段。"
        "不要判断是哪一个todo。"
        "如果用户没有要求修改某个字段，则不要返回该字段。"
        "deadline如果返回，必须是完整日期时间。"
        "格式必须是YYYY-MM-DD HH:MM:SS。"
        f"当前时间是：{now_time}"
        f"用户要求：{message}"
    )


### 7、负责生成AI匹配Todo提示词（可充当删除提示词）
#作用：根据用户描述，从数据库已有Todo列表里面找到目标id。
def match_todo_prompt(message, todos):
    return (
        "你是一个todo匹配助手。"
        "根据用户描述，从todo列表中找到用户想操作的那一个。"
        "只返回json格式。"
        "返回格式：{\"id\":数字}"
        "不要返回解释。"
        f"用户描述：{message}"
        f"todo列表：{todos}"
    )

