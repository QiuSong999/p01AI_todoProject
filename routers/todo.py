"""
Python 相对导入的语法

写法	        含义	                            例子
.	    当前目录	            from .db import xxx（同目录下的 db.py）
..	    上一级目录（父目录）	from ..db import xxx（父目录下的 db.py）
...	    上两级目录（祖父目录）	from ...db import xxx
一个点 = 向上一级；n 个点 = 向上 n 级
~~~~~~~~~~~~~~~~~
启动位置               启动命令                      main.py                             api.py                            todo.py
终端：project_1    python main.py             from api import app               from routers import todo             from db import ...
终端：python_code  python -m project_1.main   from project_1.api import app     from project_1.routers import todo   from ..db import ...

main.py 里按 Ctrl + Shift + F10，可以理解为第一种启动方式一样
~~~~~~~~~~~~~~~~~
"""
"""
用户请求
   ↓
todo.py (路由函数)
   ↓
   ├── 普通 Todo → db.py → MySQL
   │
   └── AI Todo → agent.py → DeepSeek
"""

from fastapi import APIRouter, HTTPException,Query
import math     #为了计算总页数，向上取整时用
from typing import Literal  #为了限制输入，给出几个选项

##从db.py导入操作数据库的函数
from db import (          #db.py → 提供数据库功能
    get_todos,                  #获取查询所有函数
    get_todo_id,                #条件查询（根据id查询）
    get_todo_status,            #条件查询（根据status查询）
    get_todo_count,             #查询数据总条数的函数
    get_todo_status_count,      #查询某状态的数据总条数的函数
    add_todo,                   #获取添加数据函数
    update_all,                 #获取修改数据函数（根据id修改status和deadline）
    delete_todo                 ##获取删除数据函数
)

###从ai.py导入AI总入口函数
from ai.agent import todo_by_AI
"""
用户输入自然语言后，由AI判断操作类型：
    add → 新增
    update → 修改
    delete → 删除
    search → 查询
"""


###从schema.py导入请求和响应的数据模板
from schema import (   #schema.py  → 提供数据模型
    TodoResponse,       # Todo完整数据返回模板
                        # 用于：普通查询、新增成功返回、修改成功返回、
                        #  AI功能最终返回数据也会使用这个格式
    TodoPageResponse,   # 导入分页查询函数返回的模板。用于：查询多条Todo并分页返回
    CountResponse,      # 导入查询数据总条数返回数据的模板。用于：返回数据库Todo数量

    TodoAdd,        # 普通新增Todo请求模板。用于：接收用户上传的title、deadline
    TodoUpdate,     # # 普通修改Todo请求模板。用于：接收用户上传的status、deadline
    MessageResponse,        # 操作结果返回模板。用于：删除成功后返回id和message
    AITodoAdd,              # AI新增Todo请求模板。用于：接收用户输入的自然语言，例如"明天下午3点买牛肉"
)

### 0、创建一个 FastAPI 的路由器（APIRouter），并自动给这个 router 里面的所有路由统一加上 /todo
#router = APIRouter(prefix="/todo") → @router.get("/searchtodos") → 实际接口：/todo/searchtodos
router = APIRouter(prefix="/todo")      #APIRouter的核心用途——把路由拆分到不同文件
#创建 router后，路由函数就可以写在其他文件（如主应用app写在api.py文件中，而路由函数写在todo.py）里了，并用 @router 装饰。
#在把todo.py里的 router 挂载到主应用 app（在api.py文件中）上，让本文件中的路由真正生效。
"""
现在的 todo.py 里有很多 Todo 接口：
    /todos
    /todo_id/{id}
    /todo_status/{status}
    /todo_count
它们其实都属于 todo 这一类功能。所以加：
router = APIRouter(prefix="/todo")
给一组相关的接口统一加一个“总前缀”，让路由结构更清晰，也方便以后管理（只有自定义的路由才会生效，像http://127.0.0.1:8000/docs，不用加todo
"""

"""
下面是定义路由/暴漏接口
    路由 = URL 和函数的"映射表"。
    定义路由 = 告诉服务器："当有人访问这个 URL 时，执行这个函数。
    路由就是把“请求方式 + 请求路径”对应到一个 Python 函数

本py文件一运行，用户浏览器访问http://127.0.0.1:8000/，本文件就会找头上有@app.get("/")的函数，即hello()并运行它
    get → 通常用于查
    post → 通常用于新增
    put → 通常用于修改
    delete → 通常用于删除
"""

"""
todo.py
│
└── router = APIRouter()
      │
      ├── POST /todo/todobyai
      │       AI统一入口
      │
      ├── GET /todo/searchtodos
      ├── GET /todo/searchtodo_byid/{id}
      ├── POST /todo/addtodo
      ├── PUT /todo/updatetodo/{id}
      └── DELETE /todo/deletetodo/{id}
但是，真正启动 FastAPI 的是：app = FastAPI()。api.py文件中的app.include_router(),就是把router交给app
"""

### 1、 AI Todo统一入口路由函数
#用户输入自然语言，由AI判断用户想执行：新增 / 修改 / 删除 / 查询
@router.post("/todobyai")
def todobyai(request: AITodoAdd):
    result = todo_by_AI(request.message)    #AI总入口函数
    return result

"""~~~~~~~~~~~~~下面是普通操作（非AI）路由函数~~~~~~~~~~~~~"""
### 2、普通查询所有Todo，并进行分页
@router.get("/searchtodos",response_model=TodoPageResponse)   #返回的数据 按照分页查询模板
def searchtodos(page:int=Query(1,ge=1),page_size:int=Query(10,ge=1,le=100)):   #第一个参数是默认值，ge是校验规则
    #ge=1是校验规则：必须大于等于 1；   le 用来给分页参数设置一个最大值，防止客户端一次请求过大的数据量。

    total = get_todo_count()               #调用db.py文件中的查询数据总数函数，获取总数据个数
    total_pages = math.ceil(total / page_size)      #计算总页数
    result = get_todos(page, page_size)    #调用db.py文件中的查询函数，获取当前页的数据

    return {"page":page,
            "page_size":page_size,
            "total":total,
            "total_pages":total_pages,
            "data":result}
    #启动main.py文件后，网址访问：http://127.0.0.1:8000/todo/searchtodos     查询所有数据，默认返回第1页，每页10条
    #http://127.0.0.1:8000/todo/todos?page=2&page_size=10,  第2页 → 最多10条
"""
db文件中用的fetchall()  → 多条数据 → response_model = list[TodoResponse]
db文件中用的fetchone()  → 单条数据 → response_model = TodoResponse
"""

### 3、普通条件查询路由函数
## 3.1 （根据id查询）
@router.get("/searchtodo_byid/{id}", response_model=TodoResponse)  # 查询的数据只1条
def searchtodo_byid(id: int):
    result = get_todo_id(id)
    if result is None:
        raise HTTPException(status_code=404, detail="todo not found this id")  # 报错并返回给客户端
    return result  # HTTPException：异常类。在业务代码里 raise 抛出，表示"HTTP 层面的错误"
    # print("所查询的id不存在")     #只这句话不起作用，print只是把东西打印到运行 FastAPI 的终端里，浏览器/前端并不会收到这个提示
    # status_code是状态码，404表示不存在；detail是给客户端的错误说明,
    # 常见状态码标示含义: 404 → 找不到/路由路径不存在； 422 → 你给的数据不符合要求； 500 → 服务器内部出问题
    # 浏览器访问http://127.0.0.1:8000/todo/todo_id/28得到 id=28的(todo)数据
    """
    【去程】浏览器 → api.py → db.py → MySQL
    【回程】MySQL → db.py → api.py → FastAPI → JSON → 浏览器

    http://127.0.0.1:8000/todo/5，可查询id=5的数据,具体过程如下
    【浏览器】→ GET /todo/5 →【api.py】id=5 → 【db.py】get_todo(5) → 【MySQL】select * from todos where id=5 → 查询结果 
     → db.py return → api.py 的 result → return result →【FastAPI】→ JSON →【浏览器】
    """

## 3.2（根据status查询）
@router.get("/searchtodo_bystatus/{status}",response_model=TodoPageResponse)
def searchtodo_bystatus(status:Literal["pending", "completed"],
                  page:int = Query(1, ge=1),
                  page_size: int = Query(10, ge=1, le=100)
                  ):
    result = get_todo_status(status, page, page_size)
    total = get_todo_status_count(status)       #查询到某status的数据总条数
    total_pages = math.ceil(total / page_size)  #根据总条数和每页数量计算总页数
    return {
    "page": page,
    "page_size": page_size,
    "total": total,
    "total_pages": total_pages,
    "data": result}

"""
get = 我要“拿数据”       #可通过地址栏直接访问
post = 我要“新增数据”     #必须通过http://127.0.0.1:8000/docs调试
总结：
    get     → 查
    post    → 增
    put     → 改
    delete  → 删
"""

### 4、查询所有数据条数的路由函数
@router.get("/searchtodoscount",response_model=CountResponse)
def searchtodoscount():
    result = get_todo_count()
    return {"count":result}


### 5、普通新增Todo数据
@router.post("/addtodo",response_model=TodoResponse)
def addtodo(todo:TodoAdd):     #todo接受前端发过来的 JSON，要按照 TodoCreate 这个模型来接收和校验
 #这里的 todo 不是数据库里的 Todo，也不是 TodoCreate 类本身。它是：FastAPI 根据前端 JSON 创建出来的一个 TodoCreate 对象。
    new_id = add_todo(todo.title,todo.deadline)  #todo.title从Todo对象中取出title，并当作参数上传
    result = get_todo_id(new_id)
    return result

"""
用户发送 JSON
    ↓
{"title": "给阿狗发合同",
"deadline": "2026-10-03 15:00:00"}
    ↓
Todo 模型接收
    ↓
得到一个 todo 对象，即：
    todo = Todo_Create(
        title="给阿狗发合同",
        deadline="2026-10-03 15:00:00")
     ↓
 todo.title     #得到"给阿狗发合同"
 todo.deadline  #得到"2026-10-03 15:00:00"
    ↓
add_todo(title, deadline)
    ↓
db.py
    ↓
mysql
"""

### 6、普通修改Todo数据
@router.put("/updatetodo/{id}",response_model=TodoResponse)     #根据id修改
def updatetodo(id:int,todo:TodoUpdate):
    result = update_all(id, todo.status, todo.deadline)     #返回修改了几条数据
    if result == 0:
        raise HTTPException(status_code=404, detail="todo not found")
    updated_todo = get_todo_id(id)
    return updated_todo
"""路由函数负责“发现错误并抛出去”，全局异常处理器负责“统一怎么返回”"""




### 7、普通删除Todo数据
@router.delete("/deletetodo/{id}",response_model=MessageResponse)
def deletetodo(id:int):
    result = delete_todo(id)    #delete_todo(id)该函数最后返回删除数据的条数
    if result == 0:     #如果删除的数据条数为0
        raise HTTPException(status_code=404,detail="todo not found")
    return {"id":id, "message": "todo deleted"}








