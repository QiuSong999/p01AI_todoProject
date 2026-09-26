"""
DeepSeek连接
ask_deepseek()
"""

import os
from dotenv import load_dotenv  #用于加载.env文件
from openai import OpenAI

load_dotenv()      # 读取 .env 文件，把里面的环境变量加载到程序中。

### 1、创建一个 OpenAI SDK 的客户端对象。
client = OpenAI(    #创建一个用来访问大模型的客户端工具
    api_key=os.getenv("deepseek_api_key"),
    #从环境变量中获取 deepseek_api_key，作为调用模型的身份凭证。
    base_url="https://api.deepseek.com" #设置API请求地址，让OpenAI SDK把请求发送到 DeepSeek。
)
# Python程序 → client → DeepSeek API服务器 → 大模型

### 2、把调用 DeepSeek 的代码封装成函数（自己封装的**“提问函数”**。）
def ask_deepseek(message):
    try:
        response = client.chat.completions.create(         #让client向 DeepSeek 发起一次聊天请求
        model = "deepseek-flash",         #参数：用哪个模型
        messages=[{"role": "user",
                "content": message}],
        response_format={"type": "json_object"} )
            #参数：指定输出格式。设为 {"type": "json_object"} 可强制模型输出合法的 JSON 字符串
                                                        #response返回的是对象，所以可以用.的方式来取其属性
        return response.choices[0].message.content      #response 是 DeepSeek 整个响应结果，是一个对象。
        #返回的就是：从整个 response 里，找到 choices 的第一个回答，再拿这个回答里的 message。
        """
        AI最初返回的如下面类似的结：     #非字典，而是对象
            response = {
                        "id": "chatcmpl-xxx",
                        "object": "chat.completion",
                        "created": 1727000000,
                        "model": "deepseek-flash",
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": "",
                                    "tool_calls": [
                                        {
                                            "id": "call_123",
                                            "type": "function",
                                            "function": {
                                                "name": "get_pending_todos",
                                                "arguments": "{}"  }
                                        }
                                      ]
                                        },
                                "finish_reason": "tool_calls"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 100,
                            "completion_tokens": 20,
                            "total_tokens": 120
                        }}
        ~~~~~~~~~~~~~~~~~~~~~~~
        #本函数返回的是response.choices[0].message，即：
            "message"： {"role": "assistant",        #是对象，不是字典
                                "content": "",
                                "tool_calls": [{"id": "call_123",
                                                "type": "function",
                                                "function": {"name": "get_pending_todos",
                                                "arguments": "{}" }
                                             }
        也就是AI生成的文本内容。
        因为上面设置了：
        response_format={"type":"json_object"}
        所以这里通常返回JSON字符串，例如：
        '{"title":"买牛肉","deadline":"2026-09-25 15:00:00"}'
        后面通过：
        json.loads()
        转换成Python字典。

        """

    except Exception as e:
        print("ai service error:", e)
        raise Exception(f"ai service error: {e}") from e