"""AI操作单个Todo数据的业务逻辑: AI新增/修改/删除"""
"""
业务流程
    |
    |
调用prompt生成提示词
    |
    |
调用DeepSeek
"""

from ai.client import ask_deepseek
from db import (
    add_todo,
    update_all,
    delete_todo,
    get_todo_id,
    get_all_titles
)

from ai.prompt import (     #从prompt模块导入AI提示词生成函数
    add_prompt,             #生成AI新增Todo的提示词
    update_prompt,          #生成AI提取修改字段的提示词
    match_todo_prompt       #生成AI匹配目标Todo id的提示词
)


from datetime import datetime   #导入时间，让AI知道现在的时间，助于其理解我们说的明天、后天
import json     #为了把json格式转为dict字典格式
from pydantic import ValidationError
from fastapi import HTTPException


from schema import TodoAdd, AITodoUpdate


### 1、定义AI添加 Todo/数据 的业务函数
def addtodo_by_AI(message):
    try:
        now_time = datetime.now()
        result = ask_deepseek(add_prompt(message, now_time))    #add_prompt(message, now_time)是提示词
        result = json.loads(result)     #将上面“response_format=”指定的返回JSON格式的结果，转化为dict字典格式
        #转为字典格式，就可以根据键取值了

        todo = TodoAdd(**result)     #把AI给出的 title和deadline，按照 TodoAdd 这个规则创建一个数据对象。
        # 字典 -> Pydantic对象,这里会校验AI输出的数据格式
        """
        ** 作用：把字典里的键和值，拆开作为函数/类的关键字参数传进去
        TodoAdd(**result)等价于：
            TodoAdd(             #假如用户上传的title是买面包，deadline是2026-09-18 16:00:00
                title="买面包",
                deadline="2026-09-18 16:00:00")
        """
        new_id = add_todo(todo.title, todo.deadline)        #添加到数据库
        return get_todo_id(new_id)      #返回新增后的完整数据

    #AI输出的数据不符合TodoAdd要求。 例如：{"title":"买牛奶"}，缺少deadline
    except ValidationError as e:
        raise Exception("ai output data validation failed") from e


    #其他未知错误.例如：DeepSeek接口失败、json解析失败、MySQL失败
    except Exception as e:
        # raise Exception(f"ai创建todo失败：{e}")    如果错误里面包含：api key 用户信息 数据库信息 可能泄露。
        raise Exception("ai create todo failed") from e
"""
AI新增流程：
    用户message
         ↓
    DeepSeek提取title、deadline
         ↓
    json.loads()
         ↓
    TodoAdd校验
         ↓
    add_todo()
         ↓
    get_todo_id()
         ↓
    返回完整todo
"""

### 2、定义AI修改 Todo/数据 的业务函数
def updatetodo_by_AI(message):
    try:
        now_time = datetime.now()

        #第一次调用AI：作用：只负责理解用户想修改什么字段,不负责判断修改哪一个todo
        result = ask_deepseek(update_prompt(message, now_time))

        # DeepSeek返回的是JSON字符串,例如：'{"status":"completed"}'。json.loads()转换成Python字典：{"status":"completed"}
        result = json.loads(result)

        # 字典解包给Pydantic模型。例如：AITodoUpdate(status="completed")这里会检查AI返回的数据格式是否正确
        todo = AITodoUpdate(**result)
        """
        为什么这里需要Pydantic？
        因为：
        LLM输出
            ↓
        可能格式错误的数据
            ↓
        Pydantic校验
            ↓
        业务代码
            ↓
        MySQL
        LLM不能直接相信。
        """

        # 第二次调用AI：作用：根据用户描述 + 数据库已有todo，找到用户真正想修改的是哪一条数据
        titles = get_all_titles()    #获取数据库所有title，为了AI匹配
        match_result = ask_deepseek(match_todo_prompt(message, titles))

        # AI返回JSON字符串，例如：'{"id": 3}'，json.loads()将其转换成Python字典：{"id": 3}
        match_result = json.loads(match_result)
        todo_id = int(match_result["id"])
        #从字典中取出id，并转换成int类型，例如：3

        # 根据AI找到的id，利用查询数据函数找到对应的数据
        todo_data = get_todo_id(todo_id)    #返回找到的数据

        if todo_data is None:
            raise HTTPException(
                status_code=404,
                detail="todo not found"
            )

        # 如果AI返回了新的status，就使用AI的；如果AI没有返回status，就保留数据库原来的status
        status = (
            todo.status
            if todo.status is not None
            else todo_data["status"]
        )

        # 如果AI返回了新的deadline，就使用AI的；如果AI没有返回deadline，就保留数据库原来的deadline
        deadline = (
            todo.deadline
            if todo.deadline is not None
            else todo_data["deadline"]
        )

        # 根据数据库真实id修改数据
        result = update_all(        #update_all()返回修改了几条数据
            todo_data["id"],
            status,
            deadline
        )

        if result == 0:
            raise Exception("todo update failed")

        # 修改完成后重新查询最新数据返回
        return get_todo_id(todo_data["id"])

    # HTTPException需要原样抛出
    except HTTPException:
        raise

    # AI返回格式错误
    except ValidationError as e:
        raise Exception(
            "ai output data validation failed"
        ) from e

    # 其他错误
    except Exception as e:
        raise Exception("ai update todo failed") from e
"""
AI修改todo流程：

用户自然语言
    ↓
第一次DeepSeek
    ↓
提取修改字段(deadline/status)
    ↓
AITodoUpdate校验
    ↓
获取数据库title列表
    ↓
第二次DeepSeek匹配目标todo id
    ↓
根据id查询原数据
    ↓
update_all()
    ↓
返回修改后的todo
"""

"""
例如用户：
    “把买牛肉改成明天下午3点”
流程：
用户自然语言
        ↓
第一次DeepSeek
        ↓
提取需要修改的字段
        ↓
{
    "deadline":"2026-09-20 15:00:00"
}
        ↓
获取数据库所有todo标题
        ↓
第二次DeepSeek匹配目标todo
        ↓
返回todo对应id
        ↓
根据id查询数据库原数据
        ↓
合并新数据和原数据：
新的deadline/status + 原来的其他字段
        ↓
update_all(id, status, deadline)
        ↓
get_todo_id(id)
        ↓
返回修改后的完整todo
"""


### 11、定义AI删除数据函数
def deletetodo_by_AI(message):
    try:
        # 获取数据库已有todo标题
        todos = get_all_titles()

        #第二次调用AI：根据用户描述匹配具体todo
        match_result = ask_deepseek(match_todo_prompt(message, todos))


        match_result = json.loads(match_result)
        todo_id = int(match_result["id"])

        # 根据AI找到的id，删除数据库中的todo
        result = delete_todo(todo_id)       #delete_todo()返回删除了几条数据

        # 如果删除数量为0，说明没有找到对应数据
        if result == 0:
            raise HTTPException(
                status_code=404,
                detail="todo not found"
            )

        # 返回删除结果
        return {
            "id": todo_id,
            "message": "todo deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        print("真实错误:", e)
        raise
"""
AI删除流程：
    用户message
        ↓
    get_all_titles()
        ↓
     AI匹配id
        ↓
      int()
        ↓
    delete_todo()
        ↓
    返回删除结果
"""

