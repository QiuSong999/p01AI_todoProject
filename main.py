from api import app     #把 api.py 里面已经创建好的那个 app 对象拿到 main.py 来使用
import uvicorn

"""
分工：
    todo.py: 定义 Todo 接口
          ↓
    api.py:组装 FastAPI app
          ↓
    main.py:启动 app
          ↓
    浏览器 / Swagger
"""

if __name__ == "__main__":  #表示：如果这个文件是“直接运行”的（不是被别的引用“间接执行”的） → 执行下面的代码
    uvicorn.run(
        "main:app",    #"文件名:对象名"
        host="127.0.0.1",   #只允许当前这台电脑访问这个服务                host = 服务监听的地址；host="0.0.0.0"允许其他设备连接
        port=8000,          #让 Uvicorn 在 8000 这个端口启动 FastAPI。   port = 服务监听的端口，
        reload=True         #代码发生变化后，自动重新启动 FastAPI 服务。
    )

"""
整个项目工作流程：
    启动 main.py
          ↓
    main.py 导入 api.py
          ↓
    api.py 导入 todo.py
          ↓
    todo.py 导入 db.py / agent.py / schema.py
    
    即main.py启动 → 其他文件被 import 加载yin
"""