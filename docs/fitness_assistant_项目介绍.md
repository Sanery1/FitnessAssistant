# FitnessAssistant 项目介绍（基于仓库实证）

## 说明
本文档仅使用当前仓库中的代码、配置、测试与运行结果编写。

关于你提到的《峡谷智囊AI游戏助手.pdf》：当前工作区未检索到该 PDF 实体文件，因此无法从该文件中抽取目录结构并做一一映射。为避免猜测，本文采用项目内可验证信息组织内容。

## 1. 项目定位
- 项目名称：Fitness AI Assistant（见 `README.md`）
- 目标：构建可用的 AI 健身助手，覆盖训练计划、动作指导、营养建议、身体数据与进度分析。
- 运行形态：FastAPI 后端 + 静态 Web 前端。

## 2. 技术栈（来自 requirements）
- Web：FastAPI、Uvicorn、websockets
- 数据与配置：pydantic、pydantic-settings、python-dotenv
- 向量与检索：numpy、faiss-cpu
- 网络与异步：httpx、aiofiles
- 序列化：orjson

## 3. 系统架构
### 3.1 Agent 层
- OrchestratorAgent：主控编排
- FitnessCoachAgent：训练建议
- NutritionistAgent：营养建议
- DataAnalystAgent：数据分析

代码入口：`src/agents/__init__.py`

### 3.2 Tool 层
- 训练工具：`generate_workout_plan`、`get_exercise_info`
- 营养工具：`calculate_calories`、`analyze_nutrition`
- 身体工具：`calculate_bmi`、`track_body_progress`、`calculate_body_fat`

代码入口：`src/tools/__init__.py`

### 3.3 Memory 层
- 短期记忆：会话上下文
- 长期记忆：用户数据持久化

目录：`src/memory/`

### 3.4 Workflow 层
- 状态机、节点、图、执行器与管理器

代码入口：`src/workflow/__init__.py`

### 3.5 Knowledge/RAG 层
- 知识库检索模块位于 `src/knowledge/rag.py`

## 4. API 能力总览
统一前缀：`/api`

### 4.1 Chat
- `POST /api/chat/message`
- `POST /api/chat/stream`
- `GET /api/chat/history/{user_id}`
- `DELETE /api/chat/history/{user_id}`
- `GET /api/chat/tools`

### 4.2 User
- `POST /api/user/create`
- `GET /api/user/{user_id}`
- `PUT /api/user/{user_id}/profile`
- `GET /api/user/{user_id}/context`

### 4.3 Workout
- `POST /api/workout/generate-plan`
- `POST /api/workout/exercise-info`
- `POST /api/workout/save`
- `GET /api/workout/history/{user_id}`

### 4.4 Nutrition
- `POST /api/nutrition/calculate-calories`
- `POST /api/nutrition/analyze`
- `GET /api/nutrition/food-database`

### 4.5 Body
- `POST /api/body/calculate-bmi`
- `POST /api/body/calculate-body-fat`
- `POST /api/body/track-progress`
- `POST /api/body/save`
- `GET /api/body/history/{user_id}`

## 5. 可运行性验证（本次实测）
使用环境：`D:/Code/Project/FitnessAssitant/.venv`

### 5.1 全量测试
执行命令：
- `d:/Code/Project/FitnessAssitant/.venv/Scripts/python.exe tests/run_tests.py`

结果：通过。
覆盖项包括：
- Tool System Tests
- LLM Client Utility Tests
- Memory System Tests
- Workflow System Tests
- Chat Route Tests
- API Integration Tests
- API Edge-case Tests
- Performance Baseline Tests

### 5.2 服务启动与健康检查
执行命令：
- 启动：`d:/Code/Project/FitnessAssitant/.venv/Scripts/python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8010`
- 健康检查：`/health`

实测响应：
- `{"status":"ok","version":"0.1.0"}`

结论：项目可在指定 `.venv` 环境下跑通。

## 6. 工程化与交付状态
- 已有 CI：`.github/workflows/ci.yml`
- 阶段任务记录：`tasks/todo.md`
- 当前测试入口：`tests/run_tests.py`

## 7. 边界与已知事实
- 本文未使用未验证信息。
- PDF 框架映射未完成的唯一原因是：工作区内不存在该 PDF 文件，无法读取其目录结构。
- 若你提供 PDF 的实际文件路径（放入仓库后），可在此文档基础上补充“逐章映射版”。
