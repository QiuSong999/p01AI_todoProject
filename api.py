"""FastAPI应用配置: todo.py 负责“定义有哪些 Todo 接口”，api.py 负责“把这些接口装进整个 FastAPI 应用”："""
"""
创建app
注册router
注册异常处理
配置日志
"""

#~~~~~~~~~~~~~
from routers import todo    #要使用 project_1/routers/todo.py 里面的东西。
#把整个 todo.py 模块导入进来，并给它一个名字
# 之后要通过：todo.xxx来访问里面的东西。

from fastapi import FastAPI
from fastapi import HTTPException            #HTTPException：异常类。在业务代码里 raise 抛出，表示"HTTP 层面的错误"
from pydantic import ValidationError         #导入 Pydantic 的校验失败异常类，用来捕获"数据不符合模型要求"时抛出的错误
from fastapi.exceptions import RequestValidationError       #导入 FastAPI 的请求校验异常类，用来自定义处理"请求参数不合法"的错误

from fastapi.responses import JSONResponse   #JSONResponse：响应类。手动构造 JSON 格式的 HTTP 响应，可精确控制状态码/headers

import logging      #把 Python 自带的"日志模块"导入。下面是给 logging 设置基本配置，并规定从 INFO 级别开始记录日志
logging.basicConfig(level=logging.INFO)   #logging 的"全局配置"，只需在程序开头调用一次，之后所有日志都按这个配置输出，高于info级别输出
    #logging = 程序运行日志工具；basicConfig = 给 logging 设置基本规则。 level=告诉 logging：从 INFO 这个级别开始记录日志

### 0、注册router
app = FastAPI()
app.include_router(todo.router,tags=["todo"])
#include_router(...)是FastAPI 提供的方法。理解成：把一个 router 加入到这个 FastAPI 应用中。
# 括号里的 todo.router代表： todo.py 里面那个叫 router 的 APIRouter 对象。就是“要交给 app 的那个 router 对象”。
"""
Todo 路由集合交给 FastAPI 主应用管理。把todo.py 里面定义的所有路由，注册到 FastAPI 的 app 上
router 负责收集 Todo 路由，app.include_router(todo.router) 负责把这些路由注册到 FastAPI 主应用

tags 是给这组路由打标签，让它们在 FastAPI 自动生成的文档页面（/docs）里分类显示 （给这些路由标记为 todo 分类）
例如接口有：
    GET    /todo/searchtodos
    GET    /todo/searchtodo_byid/{id}
    POST   /todo/addtodo
    PUT    /todo/updatetodo/{id}
    DELETE /todo/deletetodo/{id}
加上tags=["todo"],Swagger 里就会把它们放在类似：
    todo
    ├── GET    /todo/searchtodos
    ├── GET    /todo/searchtodo_byid/{id}
    ├── POST   /todo/addtodo
    ├── PUT    /todo/updatetodo/{id}
    └── DELETE /todo/deletetodo/{id}
"""

"""
todo.py文件里的：
    router = APIRouter(prefix="/todo")
    
    @router.get("/todos")
    def get_todos():
    ……
    负责定义路由（创建并配置路由）
    然后本文件中的app.include_router(todo.router)负责的是：把这些路由交给 FastAPI（把路由注册到 FastAPI）。
"""
# todo.router解释： todo	是导入的模块 ；todo.router	表示模块里的 APIRouter 实例


### 1、设置根目录
@app.get("/")
def hello():
    return{"message":"hello ai todo"}

#### 2、异常处理
#注册一个全局异常处理器：当程序里抛出 HTTPException 时，不要用 FastAPI 默认的处理方式，
# 改用我写的 http_exception_handler 函数来处理。 ⭐路由函数负责“发现错误并抛出去”，全局异常处理器负责“统一怎么返回”

## 2.1 创建“负责处理HTTPException异常的”处理器
@app.exception_handler(HTTPException)       #指定要捕获的异常类型
async def http_exception_handler(request, exc):    #request发生错误的那一次HTTP请求；exc为这次请求产生的异常
    #exc.status_code可得到状态码；exc.detail可以的到错误说明 （status_code→是多少号；detail→是什么错）
    return JSONResponse(        #JSONResponse：响应类。手动构造 JSON 格式的 HTTP 响应，可精确控制状态码/headers
        status_code=exc.status_code,        #HTTPException→ 属于已经明确的业务/HTTP错误
        content={"error": exc.detail}       # → 可以把具体信息告诉用户
    )

"""
request → 这次 /todo/9999 请求
exc → HTTPException(status_code=404, detail="todo not found")
完整的异常处理链：
todo_id/99
    ↓
get_todo_id(99)
    ↓
result is None
    ↓
raise HTTPException(404, ...)
    ↓
@app.exception_handler(HTTPException)
    ↓
http_exception_handler()
    ↓
JSONResponse
    ↓
404 + {"error": "todo not found this id"}
"""
"""
HTTPException   →  我主动判断“这个业务有问题”   (FastAPI 里专门表示 HTTP 层面的业务错误)
Exception       →  程序出现了一个没预料到的问题  (Python 程序运行过程中出现的异常的“总类”)
                   如number = 10 / 0，报ZeroDivisionError；print(name)，但name未定义，报NameError，这些都是Exception
ValidationError →  数据格式/规则不符合要求
RequestValidationError → 处理「进入接口的数据」不符合要求 （本项目用来处理用户上传数据不符要求）
~~~~~~~~~~~~~~~~~~
   HTTPException
         ↓
业务代码主动告诉 FastAPI：
“这里应该返回一个 HTTP 错误”

     Exception
         ↓
   Python 程序运行时：
    “这里发生了异常”
业务上预期的错误→ HTTPException→ 例如 404

程序意外发生的错误→ Exception→ 例如 500
"""


## 2.2 RequestValidationError = "用户传进来的"数据不符合接口要求
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request, exc):

    return JSONResponse(
        status_code=422,
        content={
            "error":"request data invalid",
            "detail":exc.errors()
        }
    )

"""
RequestValidationError → 处理「进入接口的数据」不符合要求 （本项目用来处理用户上传数据不符要求）
ValidationError → 处理「程序内部生成的数据」不符合要求（本项目用来处理大模型的输出不符要求）
    目的是把 FastAPI 的“入口数据校验”和 AI 应用里的“模型输出校验”区分开
"""

## 2.3 捕获"数据不符合模型要求"时抛出的错误(程序内部拿到的数据不符合要求)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):

    return JSONResponse(
        status_code=422,
        content={
            "error":"data validation failed",
            "detail":exc.errors()
        }
    )

## 2.4 普通的、没有被其他专门处理器处理的 Exception（全局异常）
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logging.exception("unexpected server error")      #把真正发生的错误记录到服务器日志里(给开发者看)
    """
    方法	                     用途	    是否带堆栈
    logging.info()	        普通信息	        ❌
    logging.error()	        记录错误消息	    ❌
    logging.exception()	    记录异常发生位置	✅
    """
    """
    发生异常
       ↓
    exc 拿到真正的异常
       ↓
    logging.error(exc)   ← 记录给开发者
       ↓
    JSONResponse         ← 返回给用户
       ↓
    500 + server internal error
    """

    # 普通 Exception → 可能是数据库、代码、第三方API等内部错误 → 用户只看到统一的500错误 → 真实错误记录到服务器日志
    return JSONResponse(
        status_code=500,
        content={"error": "server internal error"}      #(给用户看)
    )

"""
三种异常处理机制：
                 请求
                   |
                   ↓
              FastAPI接口
                   |
        -----------------------
        |          |          |
        ↓          ↓          ↓

 HTTPException  ValidationError  Exception

        |          |          |
        ↓          ↓          ↓

业务错误       数据错误      程序错误

        |          |          |

        ↓          ↓          ↓

       4xx        422        500
"""

