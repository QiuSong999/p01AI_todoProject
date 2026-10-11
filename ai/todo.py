"""AI操作单个Todo数据的业务逻辑: AI新增/修改/删除"""
"""
业务流程
    |
调用prompt生成提示词
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


from schema import TodoAdd, AITodoUpdate,AITodoMatch


### 1、定义AI添加 Todo/数据 的业务函数
def addtodo_by_AI(message):
    try:
        now_time = datetime.now()   #获取当前时间，帮助大模型理解“明天”“后天下午”等相对时间。
        result = ask_deepseek(add_prompt(message, now_time))
        #add_prompt(message, now_time)是提示词 —— 从用户自然语言中提取新增数据的：title、 deadline

        result = json.loads(result)
        #将上面大模型指定的返回JSON格式的结果，转化为dict字典格式（转为字典格式，就可以根据键取值了）

        todo = TodoAdd(**result)     #把AI提取出来的要新增数据的 title和deadline，按照TodoAdd这个规则创建一个数据对象。
        # 字典 → Pydantic对象 , 这里会校验AI输出的数据格式是否满足TodoAdd
        """
        ** 作用：把字典里的键和值，拆开作为函数/类的关键字参数传进去
        如：result={"title":"买面包","deadline":"2026-09-18 16:00:00"}
        TodoAdd(**result)等价于：
            TodoAdd(title="买面包",deadline="2026-09-18 16:00:00")
        """

        new_id = add_todo(todo.title, todo.deadline)      #add_todo是添加到数据库的实际底层操作，该函数返回新增数据的id
        return get_todo_id(new_id)                        #返回新增后的完整数据

    #处理：AI输出的数据不符合TodoAdd要求。 例如：{"title":"买牛奶"}，缺少deadline
    except ValidationError as e:    #ValidationError → 数据校验失败
        # 如果try 块里抛了 ValidationError，就进入这个分支，异常对象叫 e
        raise Exception("ai output data validation failed") from e
        # 抛出一个新的Exception，并把原始的ValidationError挂在它后面。把原来的 ValidationError 转换成了普通 Exception。
        # 因此，如果这个新异常继续传到 api.py，通常会由 global_exception_handler() 处理，返回 HTTP 500，
        # 而不是进入你注册的 ValidationError 处理器。原始校验异常不会以原类型继续向上传递。
    #ValidationError包含于Exception(见下面注释)，所以ValidationError要写在Exception上面，先处理
    # ⭐先捕获需要特殊处理的异常，再捕获通用的Exception

    #其他未知错误.例如：DeepSeek接口失败、json解析失败、MySQL失败
    except Exception as e:
        # raise Exception(f"ai创建todo失败：{e}")    如果错误里面包含：api key 用户信息 数据库信息 可能泄露。
        raise Exception("ai create todo failed") from e
"""
常见异常：
    BaseException                         ← Python 所有异常的根
        └── Exception                     ← 业务异常父类
             │
             ├── 【Python 内置/标准库异常】
             │    ├── ValueError             ← 值不对
             │    │    └── JSONDecodeError   ← json 解析失败
             │    ├── TypeError              ← 类型不对
             │    ├── KeyError               ← 字典键不存在
             │    ├── IndexError             ← 索引越界
             │    └── AttributeError         ← 属性不存在
             │
             ├── 【Pydantic 异常】
             │    └── ValidationError        ← 数据校验失败
             │
             └── 【FastAPI / Starlette 异常】
                  ├── HTTPException          ← 主动抛的 HTTP 错误（404/400/500）
                  └── RequestValidationError ← 请求参数校验失败（422）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AI新增流程：
    用户自然语言
      ↓
    add_prompt()
          ↓
    ask_deepseek()
          ↓
    JSON 字符串
          ↓
    json.loads()
          ↓
    Python 字典
          ↓
    TodoAdd(**result)
          ↓
    Pydantic 校验后的对象
          ↓
    add_todo()
          ↓
    写入 MySQL，得到新 ID
          ↓
    get_todo_id()
          ↓
    返回新增后的完整记录
"""


### 2、定义AI修改 Todo/数据 的业务函数
def updatetodo_by_AI(message):
    try:
        now_time = datetime.now()

        #第一次调用AI：作用：只负责理解用户想修改什么字段,不负责判断修改哪一个todo
        result = ask_deepseek(update_prompt(message, now_time))
        #update_prompt提示词负责让LLM提取用户想修改的字段

        result = json.loads(result)     #转化成dict方便后续校验和取值
        # DeepSeek返回的是JSON字符串,例如：'{"status":"completed"}'。
        # json.loads()将其转换成Python字典：{"status":"completed"}

        # 字典解包给Pydantic模型。例如：AITodoUpdate(status="completed")这里会检查AI返回的数据格式是否正确
        todo = AITodoUpdate(**result)
        # 为什么这里需要Pydantic？
        # 因为：LLM输出 → 可能格式错误的数据 → Pydantic校验 → 业务代码 → MySQL（LLM不能直接相信）

        #~~~~~~~~~~~~~~~~~~（第一次：提取修改内容；第二次：匹配要修改的待办）
        # 第二次调用AI：作用：根据用户描述 + 数据库已有todo，找到用户真正想修改的是哪一条数据
        titles = get_all_titles()    #获取数据库所有title，为了AI匹配
        match_result = ask_deepseek(match_todo_prompt(message, titles))
        #match_todo_prompt提示词：根据用户描述，从数据库已有Todo列表里面找到目标事项的 id

        match_result = json.loads(match_result)
        # AI返回JSON字符串，例如：'{"id": 3}'，json.loads()将其转换成Python字典：{"id": 3}

        todo_match = AITodoMatch(**match_result)    # 使用Pydantic模型校验AI返回的数据
        todo_id = todo_match.id                     #从校验通过的模型对象中获取目标Todo的id，例如：3
        todo_data = get_todo_id(todo_id)    # 利用根据id查询数据函数找到对应的待修改的数据

        if todo_data is None:               #没找到相应数据，抛HTTPException
            raise HTTPException(
                status_code=404,
                detail="todo not found"
            )

        # 如果 AI 提取出了新标题，就使用新标题；否则保留数据库原来的标题
        title = (
            todo.title      #todo为AI提取出来的，并经过AITodoUpdate检验过的“修改的字段” —— 对象
            if todo.title is not None   #判断字段是否提供了新值
            else todo_data["title"]     #todo_data为原始待修改的数据
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

        # 根据数据库真实id修改数据      #（真正的修改函数）
        result = update_all(        #update_all()返回修改了几条数据
            todo_data["id"],
            title,
            status,
            deadline
        )

        if result == 0:     #发现没有记录被修改时，停止正常返回流程，报告操作没有达到预期。
            raise Exception("todo update failed")

        # 修改完成后重新查询最新数据返回
        return get_todo_id(todo_data["id"])

    # HTTPException需要原样抛出
    except HTTPException:
        raise       #捕获 HTTPException 后原样重新抛出，保留原来的 HTTP 状态码和错误信息
    # raise Exception("...") from e创建新的通用异常，并保留原始异常原因
    # except HTTPException:  raise：原样重新抛出HTTP异常，保留其类型和信息

    # AI返回格式错误
    except ValidationError as e:    #ValidationError → 数据校验失败
        raise Exception(
            "ai output data validation failed"
        ) from e

    # 其他错误
    except Exception as e:
        raise Exception("ai update todo failed") from e
"""
AI 修改 Todo 流程：
    用户自然语言
        ↓
    第一次 DeepSeek
        ↓
    提取需要修改的字段（title / deadline / status 等）
        ↓
    json.loads() 解析 JSON 字符串
        ↓
    AITodoUpdate 校验并生成模型“对象”
        ↓
    获取数据库中现有的 todo title 列表
        ↓
    第二次 DeepSeek 匹配目标 todo id
        ↓
    根据 todo id 查询原始数据
        ↓
    合并新旧字段（新值优先，未提供新值则保留原值）
        ↓
    update_all() 更新数据库
        ↓
    重新查询更新后的 todo
        ↓
    返回修改后的 todo
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
        todos = get_all_titles()    # 获取数据库已有todo标题

        #第二次调用AI：根据用户描述匹配具体todo
        match_result = ask_deepseek(match_todo_prompt(message, todos))
        #根据用户的message，从现有todos里面匹配到要修改数据的id
        match_result = json.loads(match_result)
        todo_match = AITodoMatch(**match_result)    # 使用 Pydantic 校验 AI 返回的数据结构和 id
        todo_id = todo_match.id                      #从 Pydantic 模型对象中获取 id

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
     AI匹配待删除事项的id
        ↓
      int()
        ↓
    delete_todo() ：根据id删除
        ↓
    返回删除结果
"""

#~~~~~~~~~~~~~~
"""
操作   大模型调用次数        调用目的
新增      1               提取新增字段
修改      2               匹配待修改目标ID、提取修改字段        #在单独的search文件中
删除      1               匹配待删除目标 ID
搜索    通常2次            提取查询条件、总结查询结果

核心区别是：新增、修改、删除的现有代码把重点放在完成操作并返回数据；搜索则额外设计了结果总结环节。
如果希望新增、修改、删除也返回更自然的对话式回复，完全可以在数据库操作成功后，再把真实执行结果交给大模型。
但这属于额外设计，并不是完成数据库操作的必要条件。

另外，第二次调用大模型总结结果，也不意味着结果就一定可靠。
程序仍然应该以数据库的真实执行结果为准，不能让大模型自行编造操作成功的事实。
"""

