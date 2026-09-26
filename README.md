# AI Todo Project

一个基于 FastAPI + MySQL + DeepSeek 的 AI Todo 应用。

## 项目简介

本项目是一个 AI 大模型应用开发学习项目，在传统 Todo API 的基础上加入 DeepSeek 大模型能力，实现通过自然语言操作 Todo。

用户可以通过自然语言完成：

* 新增 Todo
* 修改 Todo
* 删除 Todo
* 查询 Todo

项目采用原生 OpenAI SDK + DeepSeek API 实现 AI 功能，暂不依赖 LangChain 等框架。

## 技术栈

* Python
* FastAPI
* Pydantic
* MySQL
* PyMySQL
* OpenAI SDK
* DeepSeek API
* Git / GitHub

## 主要功能

### Todo 基础功能

* Todo 增删改查
* 根据 ID 查询
* 根据状态查询
* 根据标题查询
* 根据截止时间查询
* Todo 分页
* Todo 数量统计
* 多条件查询

### AI 功能

* AI 意图识别
* AI 新增 Todo
* AI 修改 Todo
* AI 删除 Todo
* AI 自然语言查询 Todo
* Tool Calling
* AI 查询参数验证
* AI 查询结果自然语言生成
* 自然语言日期解析

## 项目结构

```text
p01AI_todoProject/
├── main.py
├── api.py
├── db.py
├── schema.py
├── routers/
├── ai/
├── SQL_table/
├── .env.example
└── .gitignore
```

## 运行环境

* Python 3.12
* MySQL

## 项目说明

这是一个以学习 AI 大模型应用开发为主要目的的项目。

项目首先采用原生 Python + OpenAI SDK 实现完整 AI 调用流程，后续再基于相同项目学习 LangChain、LangGraph 等框架。
