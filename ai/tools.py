"""查询工具函数"""

from db import (
    get_todo_title,
    get_todo_title_count,
    get_todos,
    get_todo_count,
    get_todo_status,
    get_todo_status_count,
    get_todo_deadline,
    get_todo_deadline_count,
    get_todo_advanced,
    get_todo_advanced_count
)

### 1、定义函数，用来当AI调用的工具
# 1.1 定义根据title查询数据的函数（工具1）
def search_todos_by_title(title, page, page_size):
    """
    给AI使用的工具函数。
    注意：这个函数不是给用户直接调用的。
    它的作用：
        把一个复杂数据库查询能力，
        包装成AI能够理解的工具。

    根据标题关键词查询Todo。
    """
    todos = get_todo_title(title, page, page_size)      #调用db文件中的“根据title查询数据的函数”
    total = get_todo_title_count(title)

    return {
        "data": todos,
        "total": total,
        "page": page,
        "page_size": page_size
    }

# 1.2 定义查询所有Todo数据的函数 （工具2）
def search_all_todos(page, page_size):
    """
    给AI使用的工具函数。
    作用：
        查询数据库中的所有Todo。
    """
    todos = get_todos(page, page_size)
    total = get_todo_count()

    return {
        "data": todos,
        "total": total,
        "page": page,
        "page_size": page_size
    }

# 1.3 定义根据status查询函数（工具3）
def search_todos_by_status(status, page, page_size):
    todos = get_todo_status(status, page, page_size)    #引用db中的get_todo_status()查询函数
    total = get_todo_status_count(status)

    return {
        "data": todos,
        "total": total,
        "page": page,
        "page_size": page_size
    }

# 1.4 定义根据deadline查询数据的函数（工具4）
def search_todos_by_deadline(start_time, end_time, page, page_size):
    """
    给AI使用的工具函数。
    作用：
        根据截止时间范围查询Todo。
    """
    todos = get_todo_deadline(
        start_time,
        end_time,
        page,
        page_size
    )

    total = get_todo_deadline_count(start_time,end_time)

    return {
        "data": todos,
        "total": total,
        "page": page,
        "page_size": page_size
    }

# 1.5 复合查询
# 上面4个：一个工具 = 一个条件。例如：status → search_todos_by_status
# 现在：一个工具 = 多个可选条件。例如：title + status + deadline
def search_todos_advanced(
        title=None,
        status=None,
        start_time=None,
        end_time=None,
        page=1,
        page_size=10):
    """
    给AI使用的高级查询工具。

    支持：
        标题关键词
        状态
        时间范围
        分页
    """

    todos = get_todo_advanced(      #根据多个可选条件查询具体的 Todo 数据
        title,
        status,
        start_time,
        end_time,
        page,
        page_size
    )

    total = get_todo_advanced_count(    #get_todo_advanced筛选出来的数据的个数
        title,
        status,
        start_time,
        end_time
    )

    return {"data": todos,
        "total": total,
        "page": page,
        "page_size": page_size}


### 2、定义AI工具列表：用于把Python中的查询工具“介绍”给大模型
#AI根据这些工具的名称、功能和参数，决定应该调用哪个工具。
ai_tools=[  # 告诉AI：“你现在拥有哪些工具可以调用”。tools=[工具1,工具2]
                # tools=[……] 作用是：把 Python 可以执行的函数“介绍给 AI”，让 AI 知道有哪些能力可以选择。
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # 第1个工具：根据标题关键词查询
                {"type": "function",  # type是告诉大模型：这个工具属于什么类型（“函数类型的工具”）
                 "function": {"name": "search_todos_by_title",  # 函数叫什么（函数名字）
                              "description": """                                    ##⭐告诉AI,这个函数干什么
                          根据待办事项标题中的关键词查询待办事项

                          适用于用户输入具体事项名称、物品名称或关键词，
                          例如：
                          - 买牛肉
                          - 买菜
                          - 开会
                          - 学习Python

                          通过标题关键词匹配查询相关待办。
                          """,
                              "parameters":  # 告诉AI这个函数需要什么参数。想调用这个函数，需要按照这个格式生成参数
                                  {"type": "object",  # 表示函数参数整体是一个 JSON 对象
                                   "properties": {  # 定义对象里面有哪些字段（2个：page和page_size）。
                                       "title": {"type": "string",  # 第1个字段title,是字符串
                                                 "description": "用户想查询的待办事项标题关键词"},  # 字段的描述
                                       "page": {"type": "integer",  # 第2个字段，该字段必须是整数
                                                "description": "要查询的页码，从1开始"},
                                       "page_size": {"type": "integer",  # 第3个字段
                                                     "description": "每页显示多少条待办事项"}},
                                   "required": ["title", "page", "page_size"]  # 标示这3个参数（title,page,page_size）必须有
                                   }}
                 },
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # 第2个工具：查询所有数据
                {"type": "function",
                 "function": {
                     "name": "search_all_todos",
                     "description": """
                        查询所有待办事项

                        适用于用户想查看全部任务，
                        例如：
                        - 查看所有任务
                        - 看一下我的待办
                        - 列出所有todo

                        不带任何筛选条件时使用该工具。
                        """,
                     "parameters": {
                         "type": "object",
                         "properties": {
                             "page": {
                                 "type": "integer",
                                 "description": "要查询的页码，从1开始"
                             },
                             "page_size": {
                                 "type": "integer",
                                 "description": "每页显示多少条待办事项"
                             }
                         },
                         "required": ["page", "page_size"]
                     }}
                 },
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # 第3个工具，根据状态查询数据
                {"type": "function",
                 "function": {"name": "search_todos_by_status",
                              "description": """
                        根据任务状态查询待办事项。

                        适用于用户提到任务完成状态，
                        例如
                        - 未完成的任务
                        - 已完成的任务
                        - pending任务
                        - completed任务

                        status参数：
                        pending表示未完成，
                        completed表示已完成。
                        """,
                              "parameters": {"type": "object",
                                             "properties": {"status": {
                                                 "type": "string",
                                                 "enum": ["pending", "completed"],
                                                 "description": "任务状态"},
                                                 "page": {"type": "integer"},
                                                 "page_size": {"type": "integer"}},
                                             "required": ["status", "page", "page_size"]}
                              }
                 },
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # 第4个工具：根据deadline查询指定范围的数据
                {"type": "function",
                 "function": {"name": "search_todos_by_deadline",
                              "description": """
                        根据截止时间范围查询待办事项。

                        适用于用户提到时间相关需求，
                        例如：
                        - 今天有哪些任务
                        - 明天有哪些任务
                        - 后天有哪些任务
                        - 某一天的任务
                        - 某个时间范围内的任务

                        需要根据用户描述生成开始时间start_time和结束时间end_time。
                        """,
                              "parameters": {
                                  "type": "object",
                                  "properties": {
                                      "start_time": {
                                          "type": "string",
                                          "description": "开始时间，格式YYYY-MM-DD HH:MM:SS"
                                      },
                                      "end_time": {
                                          "type": "string",
                                          "description": "结束时间，格式YYYY-MM-DD HH:MM:SS"
                                      },
                                      "page": {
                                          "type": "integer",
                                          "description": "查询页码，从1开始"
                                      },
                                      "page_size": {
                                          "type": "integer",
                                          "description": "每页显示数量"
                                      }
                                  },
                                  "required": [
                                      "start_time",
                                      "end_time",
                                      "page",
                                      "page_size"
                                  ]
                              }
                              }
                 },
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # 第5个工具：根据多个可选条件查询具体的 Todo 数据 函数
                {"type": "function",
                 "function": {
                     "name": "search_todos_advanced",
                     "description": """
                        根据多个条件查询待办事项。

                        支持：
                        1. 标题关键词
                        2. 任务状态
                        3. 截止时间范围

                        当用户同时提供多个查询条件时使用。

                        例如：
                        - 查询未完成的买牛肉任务
                        - 查询9月份未完成任务
                        - 查询明天的学习任务

                        """,
                     "parameters": {
                         "type": "object",
                         "properties": {

                             "title": {
                                 "type": "string",
                                 "description": "待办事项标题关键词"
                             },

                             "status": {
                                 "type": "string",
                                 "enum": [
                                     "pending",
                                     "completed"
                                 ],
                                 "description": "任务状态"
                             },

                             "start_time": {
                                 "type": "string",
                                 "description": "截止时间开始范围，例如2026-09-01 00:00:00"
                             },

                             "end_time": {
                                 "type": "string",
                                 "description": "截止时间结束范围，例如2026-09-30 23:59:59"
                             },

                             "page": {
                                 "type": "integer",
                                 "description": "页码，从1开始"
                             },

                             "page_size": {
                                 "type": "integer",
                                 "description": "每页数量"
                             }
                         }
                     }
                 }
                 }

            ]  # tools列表结尾