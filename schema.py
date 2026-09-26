"""
Pydantic模型:
    用来定义接口的数据结构。
主要作用：
1. 校验客户端提交的数据（请求模型）
    请求进入业务代码之前：
        Pydantic负责检查数据是否符合要求。
2. 规范接口返回的数据（响应模型）
    响应返回客户端之前：
        response_model负责过滤字段和规范格式。
"""
"""
模板分类：
①Request（请求模板）
    ↓
用户 / 前端 / Swagger 上传给 FastAPI
~~~~~~~

②Response（响应模板）
    ↓
FastAPI 返回给用户
~~~~~~~

③AI内部校验模板
    ↓
不是接口数据
    ↓
只是校验大模型输出是否合法
"""


from pydantic import BaseModel, Field,ConfigDict
#ConfigDict导入配置字典类，配置 Pydantic 模型（BaseModel）的底层行为
# 例如：是否允许额外字段、是否自动去除字符串空格、是否允许从 ORM 对象转换等）
from datetime import datetime
from typing import Literal  #用来限制status只能输入pending、completed

# 不同的接口，客户端需要提交的数据不同，所以使用不同的 Pydantic 模型
"""查询只需要返回模板，不需要上传模板,其他上传和返回模板看需要"""

### 1、 定义查询（非分页查询）返回模板
# db.py使用DictCursor后，MySQL返回dict。TodoResponse接着负责规定最终返回给客户端的数据字段和类型
class TodoResponse(BaseModel):       #（查询返回模板）      #查询只需要返回模板，不需要上传模板
# db.py文件中cursorclass = pymysql.cursors.DictCursormysql把查询结果变成 dict，该类是 规定/校验 api 最终响应的数据结构；
    id:int
    title:str
    deadline:datetime
    status:str
    created_at:datetime

### 2、 定义分页查询返回模板
class TodoPageResponse(BaseModel):   #（查询返回模板）
    page:int                    #当前是第几页
    page_size:int               #每页最多返回多少条
    total:int                   #数据库里一共有多少条数据
    total_pages:int             #按照每页数量，总共需要多少页
    data:list[TodoResponse]     #当前这一页实际查询出来的数据

### 3、定义AI分页查询返回模板
class AITodoPageResponse(BaseModel):
    message: str
    page: int
    page_size: int
    total: int
    total_pages: int
    data: list[TodoResponse]


### 4、定义“AI查询”的用户输入模板
class AITodoSearchRequest(BaseModel):   #负责接收和检查用户输入（接收用户给 AI 的自然语言）
    message: str = Field(min_length=1)

### 5、★以后第一次调用 DeepSeek，让它只负责判断：用户想干什么
class AIAction(BaseModel):
    action: Literal["add", "update", "delete", "search"]    #用户的动作（意图）：Todo 4个动作
    content: str        #content保存用户原话。

#用户一句话 → AIAction → 判断进入哪个函数 → addtodo_by_AI() / updatetodo_by_AI() / deletetodo_by_AI() /searchtodo_by_AI()



### 6、定义“AI查询条件”的校验模板
class AITodoSearch(BaseModel):       #检查 AI 返回的查询条件是不是我们允许的（校验 AI 返回的查询条件）
    status:Literal["pending", "completed"] | None = None
    title:str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10,ge=1, le=100)

"""" “AI查询结果”的返回模板可以直接复用class TodoResponse(BaseModel): """


"""
AITodoSearchRequest      AITodoSearch              AITodoSearchResponse(未定义，直接复用TodoResponse)
        ↓                     ↓                            ↓ 
接收用户说的话           校验 AI 判断出来的查询条件      规定我们最终给用户返回什么
"""

### 7、普通新增 Todo 上传模板
class TodoAdd(BaseModel):  #定义一个“任务数据模型”.告诉 FastAPI：以后有人新增 Todo，必须给我 title 和 deadline
    title: str = Field(min_length=1)    # 类型校验。类型是字符串，且长度至少 1
    deadline: datetime       #这个模板，把用户上传的数据，变成一个 Todo 对象
    #status设置的有默认值，不需要一定上传


### 8、AI新增 Todo 上传模板
class AITodoAdd(BaseModel):  # “AI创建Todo这个接口，用户应该提交什么样的数据”
    message: str = Field(min_length=1)
"""
TodoCreate：我要创建Todo，需要title + deadline。
AiTodoCreate：我要让AI帮我创建Todo，所以用户只需要给我message。
"""
"""普通新增返回模板、和AI新增返回模板直接用 TodoResponse(BaseModel) """


### 9、普通修改 Todo 上传模板
class TodoUpdate(BaseModel):
    # status:Literal["pending", "completed"]      #Literal[]:用来限定"值只能是某几个固定的选项之一"
    status:Literal["pending", "completed"]= Field(description="只能填写 pending 或 completed")
    #Field(description=...)提前告诉用户应该输入什么
    deadline:datetime

### 10、AI修改 Todo 上传模板
class AITodoUpdateRequest(BaseModel):   #AI 修改接口接收用户自然语言。
    message:str = Field(min_length=1)

### 11、 AI修改结果校验模板
class AITodoUpdate(BaseModel):      #用户可能只修改deadline/status，也可能两个都修改
    model_config = ConfigDict(extra="forbid")   #"forbid"	禁止多余字段
    #"ignore"——忽略多余字段（默认），直接丢掉不报错；"allow"——允许多余字段，保存下来，可访问；"forbid"——禁止多余字段，有额外字段报错422
    #"model_config = ConfigDict() — 用来设置这个模型的全局行为（比如怎么处理多余字段、怎么处理空格等）
    #不写 model_config = ConfigDict(...) 时，Pydantic v2 默认就是 extra="ignore"，如上面定义的几个类就没写，采取igonre
    """区别：
                写法	                     层级	      影响范围
    title: str = Field(min_length=1)	字段级	只影响 title 这一个字段
    model_config = ConfigDict(...)	    模型级	影响整个模型（所有字段）
    """
    deadline:datetime | None = None     #deadline 可以有，也可以没有。
    status: Literal["pending", "completed"] | None = None           #status 可以有，也可以没有。
# 如果 extra="ignore"（默认）：这些多余字段被静默丢弃，你根本不知道 AI"乱返回"了。
# 如果 extra="forbid"：直接报错，你立刻发现"AI 返回格式不对"，可以调整提示词或模型，所以这个类要加上

"""普通修改返回模板 和 AI修改返回模板 也用TodoResponse(BaseModel)"""

### 12、删除Todo返回模型
class MessageResponse(BaseModel):   #用于：普通删除和 AI 删除成功后的返回
    id:int
    message:str

### 13、AI删除 Todo 上传模板
class AITodoDelete(BaseModel):          #用于：接收用户发送给 AI 删除接口的自然语言
    message:str = Field(min_length=1)

### 14、查询数据条数返回模板
class CountResponse(BaseModel):
    count:int

"""
打开http://127.0.0.1:8000/docs，发现下面有Schema，可是里面怎么有
HTTPValidationError 、ValidationError 这两个没定义的模板呢？
    这是 FastAPI 自动生成的错误响应 Schema。
    不需要在 schema.py 里定义它们，也不需要删除或处理它们。
    它们只是 Swagger/OpenAPI 为了描述“请求参数校验失败时返回什么”而自动生成的文档模型。

所以目前看到这两个，属于正常现象
为什么会自动出现？
    因为你的接口里有参数校验。
        比如：
        def todos(
            page: int = Query(1, ge=1),
            page_size: int = Query(10, ge=1, le=100)
        ):
        如果前端传：?page=abc
        或者：?page=0
        FastAPI 会发现参数不符合要求，于是自动返回 422 参数校验错误。
        FastAPI 为了让 Swagger 文档知道这种错误长什么样，就自动生成了：
"""
"""
模板	                   类型
TodoResponse	      返 回
TodoPageResponse	  返 回
MessageResponse	      返 回
CountResponse	      返 回
TodoAdd	              上 传
AITodoAdd	          上 传
TodoUpdate	          上 传
AITodoUpdateRequest	  上 传
AITodoDelete	      上 传
AITodoUpdate	    AI内部校验
"""

