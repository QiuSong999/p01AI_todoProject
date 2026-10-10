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
# todo.router解释： todo	是导入的模块 ；todo.router	表示模块里的 APIRouter 实例
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


### 1、设置根目录
@app.get("/")
def hello():
    return{"message":"hello ai todo"}

#### 2、异常处理
#注册一个全局异常处理器：当程序里抛出 HTTPException 时，不要用 FastAPI 默认的处理方式，
# 改用我写的 http_exception_handler 函数来处理。 ⭐路由函数负责“发现错误并抛出去”，全局异常处理器负责“统一怎么返回”

## 2.1 创建“负责处理HTTPException异常的”处理器
#作用：规定 HTTPException 出现时，如何生成返回给客户端的 HTTP 响应
"""
其中：
    app：创建的 FastAPI应用对象，通常来自 app = FastAPI()；
    exception_handler：FastAPI 提供的方法，用来注册异常处理函数；
    HTTPException：指定要处理的异常类型。

    @app.exception_handler(HTTPException)整体意思就是：
    向FastAPI注册一个规则：当请求处理过程中出现需要由这个处理器处理的 HTTPException 时，使用对应的函数处理它。
"""
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):    #request为发生错误的那一次HTTP请求；exc为这次请求产生的HTTPException对象
    """
    :param request: 代表发生异常的那一次 HTTP 请求,例如，用户通过 Swagger 请求：GET /todo/9999
                    那么 request 就代表这次请求，包含请求相关的信息。
    :param exc: 代表这次请求过程中产生的异常对象,如ai/todo中的deletetodo_by_AI函数抛出
                raise HTTPException(status_code=404,detail="todo not found")，
                FastAPI调用异常处理器时，exc 就是这个 HTTPException 对象，因此下面return可以通过.status_code获取错误码
    :return:    JSONResponse是 FastAPI 使用的 Starlette 响应类，专门用于构造 JSON 格式的 HTTP 响应。
    """
    return JSONResponse(                    #JSONResponse：负责构造 HTTP 响应，并将 content 中的数据转换成 JSON 响应内容。
        status_code=exc.status_code,        #HTTPException→ 属于已经明确的业务/HTTP错误
        content={"error": exc.detail}       # → 可以把具体信息告诉用户
    )       #例如ai/todo中的deletetodo_by_AI函数raise HTTPException(status_code=404,detail="todo not found")
            #抛出的异常，经处理后，客户端收到{"error": "todo not found"}。就处理好了

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
    # request：发生错误的那一次HTTP请求对象  ;  exc：捕获到的 RequestValidationError 异常对象
    return JSONResponse(
        status_code=422,        # 直接指定 HTTP 响应状态码为 422，表示请求数据校验失败
        content={
            "error":"request data invalid",  # 返回统一的错误提示
            "detail":exc.errors()           #errors() 是 ValidationError 提供的一个方法，用来获取数据校验失败的详细信息。
        }
    )

"""
RequestValidationError： 处理进入 FastAPI 接口的请求数据不符合要求的情况。 
    例如：用户漏传必填参数、传入的数据类型不正确。 
ValidationError： 处理 Pydantic 模型校验失败的情况。 例如：程序内部将大模型输出的数据交给 Pydantic 模型校验， 
    但大模型输出的数据不符合模型定义的字段或类型要求。 
注意： 两种异常都可以通过 exc.errors() 获取具体的校验错误详情。 但它们的异常类型和典型触发场景不同。
"""

## 2.3 捕获"数据不符合模型要求"时抛出的错误(程序内部拿到的数据不符合要求):Pydantic 模型校验失败
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    # request：发生错误的 HTTP 请求对象  ； exc：捕获到的 ValidationError 异常对象
    return JSONResponse(
        status_code=422,    #Pydantic的 ValidationError对象通常没有 status_code 这个属性，所以不能直接使用 exc.status_code
        content={
            "error":"data validation failed",
            "detail":exc.errors()   #Pydantic的 ValidationError通常没有 detail 和 status_code 这两个属性，但它有 errors() 这个方法
        }
    )

## 2.4 普通的、没有被其他专门处理器处理的 Exception（全局异常）
# 当程序出现未预料到的异常，并且该异常由这个处理器接管时，把真实错误记录到服务器日志中，同时向客户端返回统一的 HTTP 500 响应
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
4种异常属性/方法不同
    异常类型               exc.status_code属性     exc.detail属性      exc.errors()方法
    HTTPException                   有               有              通常没有
    RequestValidationError          通常没有        通常没有             有
    Pydantic ValidationError        没有              没有              有 
     普通 Exception                 通常没有          通常没有            通常没有     

HTTPException：FastAPI 的 HTTP 异常，提供 status_code 和 detail 属性。
RequestValidationError：FastAPI 的请求校验异常，提供 errors() 方法获取请求数据的校验错误详情。
Pydantic ValidationError：提供 errors() 方法获取模型校验错误详情。
普通 Exception：基础异常类型，不保证具有上述属性或方法；具体取决于实际的异常子类。 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
4种异常处理器：
                    客户端请求
                        |
                        ↓
                   FastAPI 接口
                        |
          ┌─────────────┴─────────────┐
          ↓                           ↓
     请求数据校验                  接口业务代码执行
          |                           |
          ↓                ┌──────────┼─────────────────┐
 RequestValidationError    ↓          ↓                 ↓
          |          HTTPException  ValidationError  Exception
          ↓                ↓              ↓             ↓
  用户传入的请求数据    主动抛出的        Pydantic模型      未预料到的
  不符合接口要求        HTTP异常          校验失败         程序异常
          |                |              |              |
          ↓                ↓              ↓              ↓
  request_validation   http_exception  validation   global_exception
  _exception_handler   _handler        _handler      _handler
          |                |              |               |
          ↓                ↓              ↓               ↓
     状态码 422       使用异常自带的       状态码 422        状态码 500
                     status_code          |               |
          |                |              |               |
          ↓                ↓              ↓               ↓
     返回请求校验      返回 HTTP           返回模型          记录异常日志，
     错误详情          错误信息            校验错误详情      返回统一错误信息
"""

